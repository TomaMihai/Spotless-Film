import time
import threading
import numpy as np
from PIL import Image
from image_processing import ImageProcessingService, ProcessingTask
from dust_removal_state import ToolMode, ProcessingMode
import gc

def detect_dust(app):
    """Detect dust in the selected image"""
    print(f"🔍 Detect dust called")
    print(f"🔍 Selected image: {app.state.selected_image is not None}")
    print(f"🔍 U-Net model: {app.state.unet_model is not None}")
    print(f"🔍 Is detecting: {app.state.processing_state.is_detecting}")
    print(f"🔍 Is removing: {app.state.processing_state.is_removing}")
    print(f"🔍 Can detect dust: {app.state.can_detect_dust}")
    
    # Deselect active tools during generation for clarity
    app.state.set_tool_mode(ToolMode.NONE)

    if not app.state.can_detect_dust:
        print("❌ Cannot detect dust - preconditions not met")
        return
    
    app.state.processing_state.is_detecting = True
    app.state.notify_observers()
    
    def progress_callback(progress: float):
        app.root.after_idle(lambda: app.status_label.configure(
            text=f"Detecting dust... {int(progress * 100)}%"
        ))
    
    def completion_callback(result: np.ndarray, processing_time: float):
        try:
            app.state.raw_prediction_mask = result
            app.state.processing_state.processing_time = processing_time
            
            # Create initial binary mask
            app.update_dust_mask_with_threshold()
            
            # Store original mask for brush modifications
            app.state.original_dust_mask = app.state.dust_mask.copy() if app.state.dust_mask else None
            
            # Create low-res mask for performance
            app.state.create_low_res_mask()
            
            # Clear undo history and save initial state
            app.state.clear_mask_history()
            if app.state.dust_mask:
                app.state.save_mask_to_history()
            
            app.state.processing_state.is_detecting = False
            app.status_label.configure(text=f"Dust detected in {processing_time:.2f}s", text_color="green")
            app.state.notify_observers()
            
            print(f"✅ Dust detection completed in {processing_time:.2f}s")
            
        except Exception as e:
            app.handle_processing_error(e, "dust detection")
    
    def error_callback(error: Exception):
        app.handle_processing_error(error, "dust detection")
    
    # Start processing task using the simple method (matches Swift macOS app)
    def detect_worker():
        try:
            print("🔍 Starting dust detection...")
            start_time = time.time()
            
            # Use the exact prediction method from main.ipynb
            result = ImageProcessingService.predict_dust_mask(
                app.state.unet_model,
                app.state.selected_image,
                threshold=0.5,  # Default threshold, will be adjustable
                window_size=1024,
                stride=512,
                device=app.state.device,
                progress_callback=progress_callback
            )
            
            processing_time = time.time() - start_time
            completion_callback(result, processing_time)
            
        except Exception as e:
            error_callback(e)
    
    app.processing_task = threading.Thread(target=detect_worker)
    app.processing_task.daemon = True
    
    app.processing_task.start()

def remove_dust(app):
    """Remove dust using AI inpainting"""
    print(f"🎯 Remove dust called - can_remove_dust: {app.state.can_remove_dust}")
    print(f"🎯 State check - dust_mask: {app.state.dust_mask is not None}, is_detecting: {app.state.processing_state.is_detecting}, is_removing: {app.state.processing_state.is_removing}")
    
    if not app.state.can_remove_dust:
        print("❌ Cannot remove dust - preconditions not met")
        return
    
    # Toggle overlay visibility when starting removal, per requested UX
    try:
        app.toggle_overlay()
    except Exception as _e:
        print(f"⚠️ Overlay toggle failed (non-blocking): {_e}")
    
    # Deselect active tools when generating
    app.state.set_tool_mode(ToolMode.NONE)

    # 1) Generate a fast preview inpaint immediately for responsiveness (2K preview path)
    try:
        if app.preview_selected_image is not None and app.state.dust_mask is not None:
            # Build a preview-sized mask
            preview_size = app.preview_selected_image.size
            preview_mask = app.state.dust_mask.resize(preview_size, Image.Resampling.NEAREST)
            # Dilate at fixed radius 5 in preview scale
            preview_mask_dilated = ImageProcessingService.dilate_mask(preview_mask, kernel_size=5)
            # Inpaint once on preview
            preview_processed = perform_cv2_inpainting(app, app.preview_selected_image.convert('RGB'), preview_mask_dilated)
            app.preview_processed_image = preview_processed
            # Switch view for quick feedback
            app.state.set_processing_mode(ProcessingMode.SPLIT_SLIDER)
            app.state.notify_observers()
            print("🎯 Preview inpaint generated for instant feedback")
            # Ensure active view updates immediately
            # Invalidate split cache so new preview is used
            app._split_cached_signature = None
            app.display_image()
    except Exception as e:
        print(f"⚠️ Preview inpaint failed: {e}")

    app.state.processing_state.is_removing = True
    app.state.notify_observers()
    
    def completion_callback(result: Image.Image, processing_time: float):
        # Schedule GUI updates on main thread
        def update_ui():
            try:
                print(f"🎯 Completion callback called with result: {type(result)}, time: {processing_time:.2f}s")
                app.state.processed_image = result
                print(f"🎯 Processed image set: {app.state.processed_image is not None}")
                app.state.processing_state.processing_time = processing_time
                app.state.processing_state.is_removing = False
                
                # Auto-switch to split view
                print(f"🎯 Switching to SPLIT_SLIDER mode...")
                app.state.set_processing_mode(ProcessingMode.SPLIT_SLIDER)
                print(f"🎯 Current processing mode: {app.state.view_state.processing_mode}")
                
                app.status_label.configure(text=f"Dust removed in {processing_time:.2f}s", text_color="green")
                
                # Force multiple UI updates to ensure refresh
                print(f"🎯 Forcing UI updates...")
                app.state.notify_observers()
                
                # Force immediate display update with processed image
                # Invalidate split cache to pick up new processed preview/full-res
                try:
                    app.preview_processed_image = app.build_preview_image(app.state.processed_image)
                except Exception as _e:
                    print(f"⚠️ Failed to build processed preview: {_e}")
                app._split_cached_signature = None
                app.root.after_idle(lambda: app.display_image())
                print(f"🎯 Direct display_image update scheduled")
                
                # Force window refresh
                app.root.after_idle(lambda: app.root.update_idletasks())
                print(f"🎯 Window refresh scheduled")
                
                print(f"✅ Dust removal completed in {processing_time:.2f}s")
                
            except Exception as e:
                print(f"❌ Error in completion callback: {e}")
                app.handle_processing_error(e, "dust removal")
        
        app.root.after_idle(update_ui)
    
    def error_callback(error: Exception):
        def handle_error():
            print(f"❌ Error callback called: {error}")
            app.handle_processing_error(error, "dust removal")
        
        app.root.after_idle(handle_error)
    
    # Start processing task
    print("🎯 Starting ProcessingTask...")
    app.processing_task = ProcessingTask(
        target_func=lambda: perform_dust_removal(app),
        callback=completion_callback,
        error_callback=error_callback
    )
    
    app.processing_task.start()
    print("🎯 ProcessingTask started")

def perform_dust_removal(app) -> Image.Image:
    """Perform the actual dust removal process using CV2 inpainting"""
    gc.collect()
    print(f"🎨 perform_dust_removal called")
    print(f"🎨 Selected image available: {app.state.selected_image is not None}")
    print(f"🎨 Dust mask available: {app.state.dust_mask is not None}")
    if not app.state.selected_image or not app.state.dust_mask:
        raise ValueError("Missing required components for dust removal")
    print("🎨 Starting CV2 inpainting process...")
    base_mask = app.state.dust_mask
    if not getattr(app.state, 'remove_scratches', True):
        from image_processing import ImageProcessingService
        base_mask = ImageProcessingService.keep_small_dust_only(base_mask)
    if getattr(app.state, 'dust_brightness_color', True):
        from image_processing import ImageProcessingService
        base_mask = ImageProcessingService.filter_mask_by_brightness_and_color(
            base_mask, app.state.selected_image, min_brightness=getattr(app.state,'min_brightness',180), max_color_diff=getattr(app.state,'max_color_diff',40))
    print("🎨 Dilating mask...")
    from image_processing import ImageProcessingService
    dilated_mask = ImageProcessingService.dilate_mask(base_mask)
    print("🎨 Converting image to RGB...")
    image_rgb = app.state.selected_image.convert('RGB')
    print("🎨 Performing CV2 inpainting...")
    inpainted = perform_cv2_inpainting(app, image_rgb, dilated_mask)
    print("🎨 Blending images...")
    final_result = ImageProcessingService.blend_images(image_rgb, inpainted, dilated_mask)
    app.preview_processed_image = app.build_preview_image(final_result)
    print("🎨 Dust removal process completed!")
    return final_result

def perform_cv2_inpainting(app, image: Image.Image, mask: Image.Image) -> Image.Image:
    """Perform single-pass CV2 TELEA inpainting (fast)."""
    import cv2
    
    # Convert PIL images to numpy arrays
    image_np = np.array(image.convert('RGB'))
    mask_np = np.array(mask.convert('L'))
    
    print(f"🔍 Image shape: {image_np.shape}, Mask shape: {mask_np.shape}")
    result = cv2.inpaint(image_np, mask_np, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    print("✅ CV2 single-pass inpainting completed (radius=5)")
    return Image.fromarray(result)