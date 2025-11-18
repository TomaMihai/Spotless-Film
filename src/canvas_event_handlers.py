from dust_removal_state import ToolMode, ProcessingMode
from image_processing import BrushTools
from PIL import Image

def on_canvas_resize(app, event):
    """Handle canvas resize"""
    if app.use_gl:
        # GL view resizes automatically; just redraw
        if hasattr(app, 'gl_view'):
            app.gl_view.after_idle(app.gl_view.redraw)
    else:
        if hasattr(app, 'photo') and app.state.selected_image:
            app.display_image()
        else:
            app.show_welcome_message()

def on_canvas_click(app, event):
    """Handle canvas click for split view interaction"""
    # Prioritize panning when space is held (even with tools selected)
    if app.state.view_state.space_key_pressed:
        app.is_panning = True
        app.last_mouse_pos = (event.x, event.y)
        return

    # Tool interactions (only when space is not pressed)
    if app.state.view_state.tool_mode == ToolMode.ERASER and app.state.dust_mask is not None:
        cw, ch = app.canvas.winfo_width(), app.canvas.winfo_height()
        app.apply_eraser_at_point((event.x, event.y), cw, ch)
        return
    if app.state.view_state.tool_mode == ToolMode.BRUSH and app.state.dust_mask is not None:
        cw, ch = app.canvas.winfo_width(), app.canvas.winfo_height()
        app.apply_brush_at_point((event.x, event.y), cw, ch)
        return

    if app.state.view_state.processing_mode == ProcessingMode.SPLIT_SLIDER and hasattr(app, 'photo_split'):
        canvas_width = app.canvas.winfo_width()
        canvas_height = app.canvas.winfo_height()
        img_left, img_top, img_w, img_h = app._get_split_bounds(canvas_width, canvas_height)
        if img_w > 0 and img_h > 0 and img_left <= event.x <= img_left + img_w and img_top <= event.y <= img_top + img_h:
            relative_x = (event.x - img_left) / float(img_w)
            app.split_position = max(0.05, min(0.95, relative_x))
            app.display_image()

def on_canvas_drag(app, event):
    """Handle canvas drag for split view interaction or panning when zoomed"""
    # Prioritize panning when space is held (even with tools selected)
    if app.state.view_state.space_key_pressed:
        # Initialize panning if not already started
        if app.last_mouse_pos is None:
            app.last_mouse_pos = (event.x, event.y)
            app.is_panning = True
            print("🔧 Panning initialized")
            return
            
        dx = event.x - app.last_mouse_pos[0]
        dy = event.y - app.last_mouse_pos[1]
        
        # Only pan if there's actual movement
        if abs(dx) > 0 or abs(dy) > 0:
            off_x, off_y = app.state.view_state.drag_offset
            app.state.view_state.drag_offset = (off_x + dx, off_y + dy)
            app.last_mouse_pos = (event.x, event.y)
            print(f"🔧 Panning: dx={dx}, dy={dy}, offset={app.state.view_state.drag_offset}")
            
            # Move existing canvas items without re-rendering
            if app.image_item_id is not None:
                canvas_w = app.canvas.winfo_width() or 1
                canvas_h = app.canvas.winfo_height() or 1
                center_x = canvas_w // 2 + int(app.state.view_state.drag_offset[0])
                center_y = canvas_h // 2 + int(app.state.view_state.drag_offset[1])
                app.canvas.coords(app.image_item_id, center_x, center_y)
                if app.overlay_item_id is not None:
                    app.canvas.coords(app.overlay_item_id, center_x, center_y)
        return

    # Tool drags (only when space is not pressed)
    if app.state.view_state.tool_mode == ToolMode.ERASER and app.state.dust_mask is not None:
        cw, ch = app.canvas.winfo_width(), app.canvas.winfo_height()
        app.apply_eraser_at_point((event.x, event.y), cw, ch)
        return
    if app.state.view_state.tool_mode == ToolMode.BRUSH and app.state.dust_mask is not None:
        cw, ch = app.canvas.winfo_width(), app.canvas.winfo_height()
        app.apply_brush_at_point((event.x, event.y), cw, ch)
        return

    # Otherwise, handle split slider dragging directly
    if app.state.view_state.processing_mode == ProcessingMode.SPLIT_SLIDER and hasattr(app, 'photo_split'):
        canvas_width = app.canvas.winfo_width()
        canvas_height = app.canvas.winfo_height()
        img_left, img_top, img_w, img_h = app._get_split_bounds(canvas_width, canvas_height)
        if img_w > 0 and img_h > 0 and img_left <= event.x <= img_left + img_w and img_top <= event.y <= img_top + img_h:
            relative_x = (event.x - img_left) / float(img_w)
            app.split_position = max(0.05, min(0.95, relative_x))
            app.display_image()

def on_mouse_wheel(app, event):
    """Smooth, cursor-anchored zoom for wheel or pinch gestures"""
    if app.use_gl:
        # For GL view, reuse the same math, then push view to GL
        # Determine scroll direction/magnitude
        raw = 0
        if hasattr(event, 'delta') and event.delta:
            raw = event.delta
        elif hasattr(event, 'num'):
            raw = 120 if event.num == 4 else -120
        if raw == 0:
            return
        step = 1.10
        factor = step if raw > 0 else 1/step
        old_zoom = float(app.state.view_state.zoom_scale)
        new_zoom = max(1.0, min(5.0, old_zoom * factor))
        if abs(new_zoom - old_zoom) < 1e-3:
            return
        # Anchor at cursor (approximate since GL computes fit internally)
        off_x, off_y = app.state.view_state.drag_offset
        app.state.view_state.drag_offset = (off_x, off_y)
        app.state.view_state.zoom_scale = new_zoom
        app.update_zoom_ui()
        app.gl_view.set_view(app.state.view_state.zoom_scale, app.state.view_state.drag_offset)
        return
    # Determine scroll direction/magnitude (supports macOS/Windows/Linux)
    raw = 0
    if hasattr(event, 'delta') and event.delta:
        raw = event.delta
    elif hasattr(event, 'num'):
        raw = 120 if event.num == 4 else -120

    if raw == 0:
        return

    # Zoom factor with smoothing
    step = 1.10
    factor = step if raw > 0 else 1/step

    # Current zoom and clamp range
    old_zoom = float(app.state.view_state.zoom_scale)
    new_zoom = max(1.0, min(5.0, old_zoom * factor))
    if abs(new_zoom - old_zoom) < 1e-3:
        return

    # Cursor-anchored zoom: adjust pan so the point under cursor stays put
    cx, cy = event.x, event.y
    off_x, off_y = app.state.view_state.drag_offset
    # Translate from canvas center to apply offset relative to center
    canvas_w = app.canvas.winfo_width() or 1
    canvas_h = app.canvas.winfo_height() or 1
    center_x = canvas_w / 2 + off_x
    center_y = canvas_h / 2 + off_y
    # Vector from current image center to cursor
    vx = cx - center_x
    vy = cy - center_y
    # How that vector changes with zoom
    scale_ratio = new_zoom / max(1e-6, old_zoom)
    new_vx = vx * scale_ratio
    new_vy = vy * scale_ratio
    # Compute new offset so the cursor-target stays stationary
    new_center_x = cx - new_vx
    new_center_y = cy - new_vy
    app.state.view_state.drag_offset = (new_center_x - canvas_w / 2, new_center_y - canvas_h / 2)

    # During fast wheel, use faster resize for responsiveness
    if app._zoom_redraw_job is None:
        app._current_resample = Image.Resampling.BILINEAR

    # Commit zoom and refresh
    app.state.view_state.zoom_scale = new_zoom
    app.update_zoom_ui()
    app.display_image()

    # Schedule a high-quality redraw after the wheel stops
    if app._zoom_redraw_job is not None:
        try:
            app.root.after_cancel(app._zoom_redraw_job)
        except Exception:
            pass
    def _finalize_redraw():
        app._current_resample = None
        app.display_image()
        app._zoom_redraw_job = None
    app._zoom_redraw_job = app.root.after(app._zoom_finalize_delay_ms, _finalize_redraw)

def on_canvas_release(app, event):
    """Handle mouse release, stop panning if needed"""
    app.is_panning = False
    app.last_mouse_pos = None
    # End brush stroke if any tool is active
    if app.state.view_state.tool_mode in (ToolMode.BRUSH, ToolMode.ERASER):
        app.state.end_brush_stroke()

def apply_eraser_at_point(app, point, canvas_width, canvas_height):
    """Apply eraser tool at given point"""
    if not app.state.dust_mask:
        return
    
    # Don't apply eraser when space key is pressed (panning mode)
    if app.state.view_state.space_key_pressed:
        return
    
    # Start brush stroke
    app.state.start_brush_stroke()
    
    # Get low-res mask for performance
    low_res_mask = app.state.get_low_res_mask()
    if not low_res_mask:
        return
    
    # Convert point to low-res coordinates
    low_res_point = app.convert_to_low_res_coordinates(point, low_res_mask.size)
    if not low_res_point:
        return
    
    # Calculate brush radius for low-res mask
    scale_factor = min(low_res_mask.size) / min(canvas_width, canvas_height)
    brush_radius = max(1, int(app.state.view_state.brush_size * scale_factor))
    
    # Apply eraser with interpolation if we have a previous point
    if app.state.last_eraser_point:
        updated_mask = BrushTools.interpolated_stroke(
            low_res_mask, app.state.last_eraser_point, low_res_point, 
            brush_radius, is_erasing=True
        )
    else:
        updated_mask = BrushTools.apply_circular_brush(
            low_res_mask, low_res_point, brush_radius, is_erasing=True
        )
    
    if updated_mask:
        app.state.update_low_res_mask(updated_mask)
        app.state.last_eraser_point = low_res_point
        app.display_image()

def apply_brush_at_point(app, point, canvas_width, canvas_height):
    """Apply brush tool at given point"""
    if not app.state.dust_mask:
        return
    
    # Don't apply brush when space key is pressed (panning mode)
    if app.state.view_state.space_key_pressed:
        return
    
    # Start brush stroke
    app.state.start_brush_stroke()
    
    # Get low-res mask for performance
    low_res_mask = app.state.get_low_res_mask()
    if not low_res_mask:
        return
    
    # Convert point to low-res coordinates
    low_res_point = app.convert_to_low_res_coordinates(point, low_res_mask.size)
    if not low_res_point:
        return
    
    # Calculate brush radius for low-res mask
    scale_factor = min(low_res_mask.size) / min(canvas_width, canvas_height)
    brush_radius = max(1, int(app.state.view_state.brush_size * scale_factor))
    
    # Apply brush with interpolation if we have a previous point
    if app.state.last_brush_point:
        updated_mask = BrushTools.interpolated_stroke(
            low_res_mask, app.state.last_brush_point, low_res_point, 
            brush_radius, is_erasing=False
        )
    else:
        updated_mask = BrushTools.apply_circular_brush(
            low_res_mask, low_res_point, brush_radius, is_erasing=False
        )
    
    if updated_mask:
        app.state.update_low_res_mask(updated_mask)
        app.state.last_brush_point = low_res_point
        app.display_image()