import threading
from pathlib import Path
from image_processing import ImageProcessingService, LamaInpainter
from image_processing import ImageProcessingService

def load_models_async(app):
    """Load models asynchronously"""
    def load_models():
        try:
            print("🤖 Starting model loading...")
            
            # Look for model files
            model_paths = find_model_files(app)
            print(f"🤖 Model paths found: {model_paths}")
            
            if model_paths['unet']:
                print(f"🤖 Loading U-Net model from: {model_paths['unet']}")
                app.state.unet_model = ImageProcessingService.load_model(
                    model_paths['unet'], app.state.device
                )
                print(f"🤖 U-Net model loaded successfully: {app.state.unet_model is not None}")
                app.root.after_idle(lambda: app.status_label.configure(text="U-Net model loaded"))
            else:
                print("❌ No U-Net model file found!")
                app.root.after_idle(lambda: app.status_label.configure(
                    text="No model file found", text_color="red"
                ))
            
            # Initialize LaMa
            print("🤖 Initializing LaMa...")
            app.lama_inpainter = LamaInpainter()
            app.state.lama_inpainter = app.lama_inpainter
            
            lama_status = "✅ Available" if app.lama_inpainter.available else "❌ Unavailable"
            print(f"🤖 LaMa status: {lama_status}")
            app.root.after_idle(lambda: app.lama_label.configure(text=f"LaMa: {lama_status}"))
            
            if app.state.unet_model:
                print("🤖 All models loaded successfully")
                app.root.after_idle(lambda: app.status_label.configure(
                    text="Ready - Drag image or use Import", text_color="green"
                ))
            else:
                print("❌ U-Net model failed to load")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            app.root.after_idle(lambda: app.status_label.configure(
                text="Model loading failed", text_color="red"
            ))
    
    thread = threading.Thread(target=load_models)
    thread.daemon = True
    thread.start()

def find_model_files(app) -> dict:
    """Find model files - prioritize the specific weights file from main.ipynb"""
    model_paths = {'unet': None, 'lama': None}
    
    # First, look for the exact weights file mentioned in main.ipynb
    exact_weight_path = Path(__file__).parent / "weights" / "v5_bce_unet_epoch30.pth"
    if exact_weight_path.exists():
        model_paths['unet'] = str(exact_weight_path)
        print(f"✅ Found exact weights file: {exact_weight_path}")
        return model_paths
    
    # Fallback: search in common locations
    search_dirs = [
        Path(__file__).parent / "weights",
        Path(__file__).parent / "checkpoints", 
        Path.cwd() / "models",
        Path.cwd() / "checkpoints",
        Path.cwd() / "weights",
        Path.cwd().parent / "models",
        Path.cwd().parent / "checkpoints",
    ]
    
    for search_dir in search_dirs:
        if search_dir.exists():
            print(f"🔍 Searching in: {search_dir}")
            # Look for U-Net models (prioritize v5 and v6 models from notebook)
            for pattern in ["v5_*.pth", "v6_*.pth", "*unet*.pth", "*.pth"]:
                unet_files = list(search_dir.glob(pattern))
                if unet_files:
                    # Sort by name to get latest version
                    unet_files.sort(reverse=True)
                    model_paths['unet'] = str(unet_files[0])
                    print(f"✅ Found weights file: {unet_files[0]}")
                    break
            
            if model_paths['unet']:
                break
    
    return model_paths

def handle_processing_error(app, error: Exception, operation: str):
    """Handle processing errors"""
    app.state.processing_state.is_detecting = False
    app.state.processing_state.is_removing = False
    error_msg = f"{operation.capitalize()} failed: {str(error)}"
    app.state.show_error(error_msg)
    app.status_label.configure(text="Error occurred", text_color="red")
    app.state.notify_observers()
    print(f"❌ {error_msg}")

def update_dust_mask_with_threshold(app):
    """Update dust mask based on current threshold"""
    if app.state.raw_prediction_mask is None or not app.state.selected_image:
        return
    
    # Create new binary mask
    new_mask = ImageProcessingService.create_binary_mask(
        app.state.raw_prediction_mask,
        app.state.processing_state.threshold,
        app.state.selected_image.size
    )
    # If user disabled scratch/lint removal, filter to keep only small dust specks
    if new_mask and not getattr(app.state, 'remove_scratches', True):
        new_mask = ImageProcessingService.keep_small_dust_only(new_mask)
    
    app.state.dust_mask = new_mask
    app.state.create_low_res_mask()
    app.state.notify_observers()

def update_dust_mask_with_threshold_realtime(app):
    """Real-time threshold updates (matches Swift app behavior)"""
    if app.state.raw_prediction_mask is None or not app.state.selected_image:
        return
    
    print(f"🎚️ Updating threshold to {app.state.processing_state.threshold:.3f}")
    
    # Create new binary mask with current threshold
    new_mask = ImageProcessingService.create_binary_mask(
        app.state.raw_prediction_mask,
        app.state.processing_state.threshold,
        app.state.selected_image.size
    )
    
    if new_mask:
        if not getattr(app.state, 'remove_scratches', True):
            new_mask = ImageProcessingService.keep_small_dust_only(new_mask)
        app.state.dust_mask = new_mask
        app.state.create_low_res_mask()
        
        # Immediately update the display
        app.update_ui()
        
        print(f"✅ Mask updated with threshold {app.state.processing_state.threshold:.3f} (filtered small dust only={not getattr(app.state,'remove_scratches', True)})")