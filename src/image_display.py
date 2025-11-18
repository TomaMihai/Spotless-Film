from PIL import Image, ImageTk
import numpy as np
from dust_removal_state import ProcessingMode

def display_image(app, image=None):
    """Display image on canvas based on current view mode"""
    try:
        # Get canvas size
        if app.use_gl:
            canvas_width = app.gl_view.width
            canvas_height = app.gl_view.height
        else:
            canvas_width = app.canvas.winfo_width()
            canvas_height = app.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Clear canvas first
        app.canvas.delete('all')
        
        # Handle different view modes
        mode = app.state.view_state.processing_mode
        print(f"🖼️ Displaying in {mode} mode")
        
        if mode == ProcessingMode.SINGLE:
            if app.use_gl:
                display_single_view_gl(app, canvas_width, canvas_height)
            else:
                display_single_view(app, canvas_width, canvas_height, image)
        elif mode == ProcessingMode.SIDE_BY_SIDE:
            display_side_by_side_view(app, canvas_width, canvas_height)
        elif mode == ProcessingMode.SPLIT_SLIDER:
            display_split_view(app, canvas_width, canvas_height)
        
    except Exception as e:
        print(f"Error displaying image: {e}")

def display_single_view(app, canvas_width, canvas_height, image=None):
    """Display single image view"""
    # Smart image selection - prefer processed image if available
    if image is None:
        if app.state.processed_image:
            image = app.preview_processed_image or app.state.processed_image
            print("🖼️ Single view: Using processed image")
        else:
            image = app.preview_selected_image or app.state.selected_image
            print("🖼️ Single view: Using selected image")
    else:
        print(f"🖼️ Single view: Using provided image")
    
    if not image:
        return
    
    # Create working image from chosen source (preview/full)
    display_image = image.copy()
    
    # Determine if we're showing processed (for info; we now allow overlay on both)
    is_processed_display = (
        (app.state.processed_image is not None) and 
        (image is app.preview_processed_image or image is app.state.processed_image)
    )
    
    # Compute base fit size within margins
    margin = 40
    base_w = canvas_width - margin
    base_h = canvas_height - margin
    img_ratio = display_image.size[0] / display_image.size[1]
    canvas_ratio = base_w / base_h if base_h > 0 else 1.0
    if img_ratio > canvas_ratio:
        fitted_w = base_w
        fitted_h = int(base_w / img_ratio)
    else:
        fitted_h = base_h
        fitted_w = int(base_h * img_ratio)

    # Apply zoom
    zoom = max(1.0, float(app.state.view_state.zoom_scale))
    disp_w = max(1, int(fitted_w * zoom))
    disp_h = max(1, int(fitted_h * zoom))

    # Choose resampling quality (interactive zoom uses faster filter)
    resample = app._current_resample or Image.Resampling.LANCZOS
    display_image = display_image.resize((disp_w, disp_h), resample)

    # Calculate position with pan offset
    off_x, off_y = app.state.view_state.drag_offset
    center_x = canvas_width // 2 + int(off_x)
    center_y = canvas_height // 2 + int(off_y)

    # Convert to PhotoImage
    app.photo = ImageTk.PhotoImage(display_image)

    # Display image centered with pan offset
    app.image_item_id = app.canvas.create_image(center_x, center_y, image=app.photo)

    # If overlay visible, render as a separate canvas image for speed
    if (app.state.dust_mask and getattr(app, 'overlay_visible', True)):
        overlay_img = create_overlay_layer(app, (disp_w, disp_h))
        if overlay_img is not None:
            app.photo_overlay = ImageTk.PhotoImage(overlay_img)
            app.overlay_item_id = app.canvas.create_image(center_x, center_y, image=app.photo_overlay)
        else:
            app.overlay_item_id = None
    else:
        app.overlay_item_id = None

    # Store bounds for hit-testing/brush mapping (top-left, size)
    app.image_item_bounds = (center_x - disp_w // 2, center_y - disp_h // 2, disp_w, disp_h)

def display_side_by_side_view(app, canvas_width, canvas_height):
    """Display side-by-side comparison view"""
    if not app.state.selected_image:
        return
    
    print("🖼️ Rendering side-by-side view")
    
    # Calculate dimensions for each side
    half_width = canvas_width // 2
    margin = 20
    
    # Original image (left side)
    original_image = app.state.selected_image.copy()
    
    # Add dust overlay to original if available and overlay is visible
    if app.state.dust_mask and getattr(app, 'overlay_visible', True):
        # Use fast overlay at display size
        pass
    
    # Resize original image
    original_image.thumbnail((half_width - margin, canvas_height - 40), Image.Resampling.LANCZOS)
    app.photo_left = ImageTk.PhotoImage(original_image)
    
    # Display original on left
    left_x = half_width // 2
    app.canvas.create_image(left_x, canvas_height // 2, image=app.photo_left)
    app.canvas.create_text(left_x, 20, text="Original", fill="white", font=("Arial", 12, "bold"))
    
    # Processed image (right side) if available
    if app.state.processed_image:
        processed_image = app.state.processed_image.copy()
        processed_image.thumbnail((half_width - margin, canvas_height - 40), Image.Resampling.LANCZOS)
        app.photo_right = ImageTk.PhotoImage(processed_image)
        
        # Display processed on right
        right_x = half_width + (half_width // 2)
        app.canvas.create_image(right_x, canvas_height // 2, image=app.photo_right)
        app.canvas.create_text(right_x, 20, text="Processed", fill="white", font=("Arial", 12, "bold"))
    else:
        # Show placeholder text
        right_x = half_width + (half_width // 2)
        app.canvas.create_text(right_x, canvas_height // 2, text="Process image to see result", 
                              fill="gray", font=("Arial", 14))
    
    # Draw separator line
    app.canvas.create_line(half_width, 0, half_width, canvas_height, fill="white", width=2)

def display_split_view(app, canvas_width, canvas_height):
    """Display split slider view with proper image compositing"""
    if not app.state.selected_image:
        return
    
    print("🖼️ Rendering split view")
    
    # If no processed image, show single view
    if not app.state.processed_image:
        display_single_view(app, canvas_width, canvas_height)
        return
    
    # Choose preview images for performance
    base_original = app.preview_selected_image or app.state.selected_image
    base_processed = app.preview_processed_image or app.state.processed_image

    # Add dust overlay to original if visible (baked-in in split)
    if app.state.dust_mask and getattr(app, 'overlay_visible', True):
        base_original = create_overlay_image(app, base_original)

    # Calculate base fit size while maintaining aspect ratio
    display_width = canvas_width - 40
    display_height = canvas_height - 40
    img_ratio = base_original.size[0] / base_original.size[1]
    canvas_ratio = display_width / display_height
    if img_ratio > canvas_ratio:
        fit_w = display_width
        fit_h = int(display_width / img_ratio)
    else:
        fit_h = display_height
        fit_w = int(display_height * img_ratio)

    # Apply zoom
    zoom = max(1.0, float(app.state.view_state.zoom_scale))
    new_width = max(1, int(fit_w * zoom))
    new_height = max(1, int(fit_h * zoom))

    # Build a signature so cache invalidates on content changes (mask/process/opacity)
    overlay_flag = bool(app.state.dust_mask and getattr(app, 'overlay_visible', True))
    mask_token = id(app.state.dust_mask) if overlay_flag else None
    orig_token = id(base_original)
    proc_token = id(base_processed)
    cache_size = (new_width, new_height)
    signature = (cache_size, orig_token, proc_token, overlay_flag, mask_token, float(getattr(app, 'overlay_opacity', 0.5)))

    # Cache resized images for current size/content to make slider smooth
    if app._split_cached_signature != signature:
        resample = app._current_resample or Image.Resampling.LANCZOS
        app._split_resized_original = base_original.resize(cache_size, resample)
        app._split_resized_processed = base_processed.resize(cache_size, resample)
        app._split_cached_size = cache_size
        app._split_cached_signature = signature
    
    # Get split position (default to middle)
    split_position = getattr(app, 'split_position', 0.5)
    split_x_image = int(cache_size[0] * split_position)
    
    # Create composite image
    composite = Image.new('RGB', cache_size)
    
    # Left side: processed image
    if split_x_image > 0:
        left_crop = app._split_resized_processed.crop((0, 0, split_x_image, cache_size[1]))
        composite.paste(left_crop, (0, 0))
    
    # Right side: original image
    if split_x_image < cache_size[0]:
        right_crop = app._split_resized_original.crop((split_x_image, 0, cache_size[0], cache_size[1]))
        composite.paste(right_crop, (split_x_image, 0))
    
    # Convert to PhotoImage
    app.photo_split = ImageTk.PhotoImage(composite)
    
    # Calculate position to center the image
    display_x = canvas_width // 2
    display_y = canvas_height // 2
    
    # Display the composite image
    split_item = app.canvas.create_image(display_x, display_y, image=app.photo_split)
    # Store bounds for tool hit-testing in split view
    app.image_item_bounds = (display_x - (cache_size[0] // 2), display_y - (cache_size[1] // 2), cache_size[0], cache_size[1])
    
    # Calculate split line position on canvas
    canvas_split_x = display_x - (cache_size[0] // 2) + split_x_image
    
    # Draw split line
    line_y1 = display_y - (cache_size[1] // 2)
    line_y2 = display_y + (cache_size[1] // 2)
    app.canvas.create_line(canvas_split_x, line_y1, canvas_split_x, line_y2, fill="white", width=3)
    
    # Add labels
    left_label_x = display_x - (cache_size[0] // 2) + (split_x_image // 2)
    right_label_x = canvas_split_x + ((display_x + (cache_size[0] // 2) - canvas_split_x) // 2)
    label_y = line_y1 + 20
    
    app.canvas.create_text(left_label_x, label_y, text="Processed", fill="white", font=("Arial", 10, "bold"))
    app.canvas.create_text(right_label_x, label_y, text="Original", fill="white", font=("Arial", 10, "bold"))

def _get_split_bounds(app, canvas_width: int, canvas_height: int):
    """Return (left, top, width, height) of the split-view image rect on the canvas."""
    # Compute the same size math used by display_split_view
    base_original = app.preview_selected_image or app.state.selected_image
    if base_original is None:
        return (0, 0, 0, 0)
    display_width = canvas_width - 40
    display_height = canvas_height - 40
    img_ratio = base_original.size[0] / base_original.size[1]
    canvas_ratio = display_width / display_height
    if img_ratio > canvas_ratio:
        fit_w = display_width
        fit_h = int(display_width / img_ratio)
    else:
        fit_h = display_height
        fit_w = int(display_height * img_ratio)
    zoom = max(1.0, float(app.state.view_state.zoom_scale))
    new_w = max(1, int(fit_w * zoom))
    new_h = max(1, int(fit_h * zoom))
    left = (canvas_width - new_w) // 2
    top = (canvas_height - new_h) // 2
    return (left, top, new_w, new_h)

def display_single_view_gl(app, canvas_width, canvas_height):
    """GL-backed single view rendering."""
    if not app.state.selected_image:
        return
    # Base image preference: processed if available
    base = (app.preview_processed_image or app.state.processed_image) if app.state.processed_image else (app.preview_selected_image or app.state.selected_image)
    overlay_img = None
    is_processed_display = (app.state.processed_image is not None) and (base is app.preview_processed_image or base is app.state.processed_image)
    if (app.state.dust_mask and getattr(app, 'overlay_visible', True) and not is_processed_display):
        # Provide an overlay RGBA the same size as base; GL scales it efficiently.
        overlay_img = create_overlay_layer(app, base.size)
    # Upload/update textures and draw
    app.gl_view.set_images(base, overlay_img)
    app.gl_view.set_view(app.state.view_state.zoom_scale, app.state.view_state.drag_offset)

def create_overlay_image(app, base_image):
    """Create image with dust overlay (matches Swift app visualization)"""
    try:
        print("🎨 Creating dust overlay...")
        
        # Convert base image to RGB if needed
        if base_image.mode != 'RGB':
            base_image = base_image.convert('RGB')
        
        # Get dust mask
        dust_mask = app.state.dust_mask
        if not dust_mask:
            return base_image
        
        # Ensure mask is same size as image
        if dust_mask.size != base_image.size:
            dust_mask = dust_mask.resize(base_image.size, Image.Resampling.NEAREST)
        
        # Convert to numpy arrays
        base_array = np.array(base_image).astype(np.float32)
        mask_array = np.array(dust_mask).astype(np.float32) / 255.0
        
        # Create colored overlay (red dust detection)
        overlay_color = np.array([255, 0, 0], dtype=np.float32)  # Red
        overlay_alpha = float(getattr(app, 'overlay_opacity', 0.5))
        
        # Apply overlay where mask is white (dust detected)
        for i in range(3):  # RGB channels
            base_array[:, :, i] = (base_array[:, :, i] * (1 - mask_array * overlay_alpha) + 
                                 overlay_color[i] * mask_array * overlay_alpha)
        
        # Convert back to image
        overlay_image = Image.fromarray(np.clip(base_array, 0, 255).astype(np.uint8))
        
        print("✅ Dust overlay created")
        return overlay_image
        
    except Exception as e:
        print(f"❌ Error creating overlay: {e}")
        return base_image

def create_overlay_layer(app, display_size):
    """Fast path: build an RGBA overlay at display size only."""
    try:
        if not app.state.dust_mask:
            return None
        # Always base overlay on the full-res mask and scale to the current display size
        mask = app.state.dust_mask
        if mask.size != display_size:
            mask = mask.resize(display_size, Image.Resampling.NEAREST)
        mask_array = np.array(mask.convert('L'), dtype=np.uint8)
        alpha = float(getattr(app, 'overlay_opacity', 0.5))
        a = (mask_array.astype(np.float32) * alpha).clip(0, 255).astype(np.uint8)
        rgb = np.zeros((display_size[1], display_size[0], 3), dtype=np.uint8)
        rgb[:, :, 0] = mask_array  # red
        rgba = np.dstack([rgb, a])
        return Image.fromarray(rgba, 'RGBA')
    except Exception:
        return None

def build_preview_image(app, image, long_side: int = 2048):
    """Create a downscaled preview with long side capped at 2K for fast display."""
    try:
        if image is None:
            return None
        w, h = image.size
        if max(w, h) <= long_side:
            return image.copy()
        if w >= h:
            new_w = long_side
            new_h = max(1, int(h * (long_side / float(w))))
        else:
            new_h = long_side
            new_w = max(1, int(w * (long_side / float(h))))
        return image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Preview build failed: {e}")
        return image