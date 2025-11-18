from dust_removal_state import ToolMode, ProcessingMode
from spotless_ui import on_mouse_motion as on_mouse_motion_helper, update_brush_cursor as update_brush_cursor_helper, hide_brush_cursor as hide_brush_cursor_helper, update_cursor_for_tool_change as update_cursor_for_tool_change_helper

def on_mouse_motion(app, event):
    on_mouse_motion_helper(app, event)

def update_brush_cursor(app):
    update_brush_cursor_helper(app)

def hide_brush_cursor(app):
    hide_brush_cursor_helper(app)

def update_cursor_for_tool_change(app):
    update_cursor_for_tool_change_helper(app)

def cycle_view_mode(app):
    """Cycle through view modes"""
    modes = [ProcessingMode.SINGLE, ProcessingMode.SIDE_BY_SIDE, ProcessingMode.SPLIT_SLIDER]
    current_index = modes.index(app.state.view_state.processing_mode)
    next_mode = modes[(current_index + 1) % len(modes)]
    set_view_mode(app, next_mode)
    
    # Update button text
    mode_text = {
        ProcessingMode.SINGLE: "🔍 Single",
        ProcessingMode.SIDE_BY_SIDE: "🔄 Side by Side",
        ProcessingMode.SPLIT_SLIDER: "✂️ Split View"
    }
    app.view_cycle_btn.configure(text=mode_text[next_mode])

def toggle_eraser_tool(app):
    """Toggle eraser tool"""
    if app.state.view_state.tool_mode == ToolMode.ERASER:
        app.state.set_tool_mode(ToolMode.NONE)
        app.eraser_btn.configure(text="⬜\nEraser", fg_color="#5A5A5A")
    else:
        app.state.set_tool_mode(ToolMode.ERASER)
        app.eraser_btn.configure(text="✅\nEraser", fg_color="#FF6B35")
        app.brush_btn.configure(text="⬛\nBrush", fg_color="#5A5A5A")
    
    # Update cursor
    app.update_cursor_for_tool_change()

def toggle_brush_tool(app):
    """Toggle brush tool"""
    if app.state.view_state.tool_mode == ToolMode.BRUSH:
        app.state.set_tool_mode(ToolMode.NONE)
        app.brush_btn.configure(text="⬛\nBrush", fg_color="#5A5A5A")
    else:
        app.state.set_tool_mode(ToolMode.BRUSH)
        app.brush_btn.configure(text="✅\nBrush", fg_color="#4CAF50")
        app.eraser_btn.configure(text="⬜\nEraser", fg_color="#5A5A5A")
    
    # Update cursor
    app.update_cursor_for_tool_change()

def on_brush_size_changed(app, value):
    """Handle brush size change"""
    size = int(float(value))
    app.state.view_state.brush_size = size
    app.brush_size_value_label.configure(text=f"{size}px")

def toggle_overlay(app):
    """Toggle dust overlay visibility"""
    app.overlay_visible = not app.overlay_visible
    if hasattr(app.state, 'view_state'):
        app.state.view_state.hide_detections = not app.overlay_visible
    
    # Update button appearance
    if app.overlay_visible:
        app.overlay_toggle_btn.configure(text="👁 Overlay", fg_color="#007AFF")
    else:
        app.overlay_toggle_btn.configure(text="👁 Hidden", fg_color="#666666")
    
    # Refresh display
    app.display_image()

def on_opacity_changed(app, value):
    """Handle opacity slider changes"""
    opacity_percent = int(value * 100)
    app.opacity_label.configure(text=f"{opacity_percent}%")
    
    # Store opacity for overlay rendering
    app.overlay_opacity = value
    
    # Refresh display if overlay is visible
    if app.overlay_visible:
        app.display_image()

def zoom_in(app):
    """Zoom in using centralized state and refresh UI"""
    print(f"[UI] zoom_in from {app.state.view_state.zoom_scale:.3f}")
    app.state.zoom_in()
    app.update_zoom_ui()
    if app.state.selected_image:
        if app.use_gl:
            app.gl_view.set_view(app.state.view_state.zoom_scale, app.state.view_state.drag_offset)
        else:
            app.display_image()

def zoom_out(app):
    """Zoom out using centralized state and refresh UI"""
    print(f"[UI] zoom_out from {app.state.view_state.zoom_scale:.3f}")
    app.state.zoom_out()
    app.update_zoom_ui()
    if app.state.selected_image:
        if app.use_gl:
            app.gl_view.set_view(app.state.view_state.zoom_scale, app.state.view_state.drag_offset)
        else:
            app.display_image()

def reset_zoom(app):
    """Reset zoom and pan"""
    print("[UI] reset_zoom")
    app.state.reset_zoom()
    app.update_zoom_ui()
    if app.state.selected_image:
        if app.use_gl:
            app.gl_view.set_view(app.state.view_state.zoom_scale, app.state.view_state.drag_offset)
        else:
            app.display_image()

def update_zoom_ui(app):
    """Update zoom label and button states to reflect current zoom"""
    if hasattr(app, 'zoom_label'):
        percent = int(app.state.view_state.zoom_scale * 100)
        app.zoom_label.configure(text=f"{percent}%")
    if hasattr(app, 'zoom_out_btn'):
        app.zoom_out_btn.configure(state=("normal" if app.state.view_state.zoom_scale > 1.0 else "disabled"))

def update_tool_buttons(app):
    """Update tool button states"""
    tool_mode = app.state.view_state.tool_mode
    
    # Reset buttons
    app.brush_btn.configure(fg_color=("gray75", "gray25"))
    app.eraser_btn.configure(fg_color=("gray75", "gray25"))
    
    # Highlight active tool
    if tool_mode == ToolMode.BRUSH:
        app.brush_btn.configure(fg_color=('#1f538d', '#14375e'))
    elif tool_mode == ToolMode.ERASER:
        app.eraser_btn.configure(fg_color=('#1f538d', '#14375e'))

def setup_keyboard_shortcuts(app):
    """Setup professional keyboard shortcuts"""
    # Global shortcuts
    app.root.bind('<Control-o>', lambda e: app.import_image())
    app.root.bind('<Control-s>', lambda e: app.export_image())
    app.root.bind('<Control-z>', lambda e: app.undo_mask_change())
    # macOS Command+Z and Meta+Z fallback
    app.root.bind('<Command-z>', lambda e: app.undo_mask_change())
    app.root.bind('<Meta-z>', lambda e: app.undo_mask_change())
    app.root.bind('<space>', lambda e: app.toggle_space_mode(True))
    app.root.bind('<KeyRelease-space>', lambda e: app.toggle_space_mode(False))
    app.root.bind('<m>', lambda e: app.toggle_dust_overlay())
    app.root.bind('<c>', lambda e: app.toggle_compare_mode())
    app.root.bind('<e>', lambda e: app.toggle_eraser_tool())
    app.root.bind('<b>', lambda e: app.toggle_brush_tool())
    
    # Focus management
    app.root.focus_set()

def toggle_dust_overlay(app):
    """Toggle dust overlay visibility (M key like Swift app)"""
    if app.state.dust_mask:
        hide_detections = getattr(app.state, 'hide_detections', False)
        app.state.hide_detections = not hide_detections
        print(f"🎭 Dust overlay: {'hidden' if app.state.hide_detections else 'visible'}")
        # Refresh display
        if app.state.selected_image:
            app.display_image()

def toggle_space_mode(app, pressed: bool):
    """Toggle space key mode for panning"""
    app.state.view_state.space_key_pressed = pressed
    # When space is released, stop any panning drag
    if not pressed:
        app.is_panning = False
        app.last_mouse_pos = None
    else:
        # When space is pressed, prepare for potential panning
        # Don't start panning until mouse is actually moved
        pass
    # Update cursor to reflect space key state
    app.update_cursor_for_tool_change()
    app.state.notify_observers()

def toggle_compare_mode(app):
    """Cycle through compare modes"""
    modes = [ProcessingMode.SINGLE, ProcessingMode.SIDE_BY_SIDE, ProcessingMode.SPLIT_SLIDER]
    current_index = modes.index(app.state.view_state.processing_mode)
    next_index = (current_index + 1) % len(modes)
    next_mode = modes[next_index]
    app.state.set_processing_mode(next_mode)

def undo_mask_change(app):
    """Undo last mask change"""
    if app.state.can_undo:
        app.state.undo_last_mask_change()

def on_threshold_changed(app, value):
    """Handle real-time threshold slider changes (matches Swift app behavior)"""
    threshold = float(value)
    
    # Update the displayed value
    app.threshold_value_label.configure(text=f"{threshold:.4f}")
    
    # Update the state threshold
    app.state.processing_state.threshold = threshold
    
    # Immediately update the dust mask if we have a prediction
    if app.state.raw_prediction_mask is not None:
        app.update_dust_mask_with_threshold_realtime()

def set_view_mode(app, mode: ProcessingMode):
    """Set processing mode and update display"""
    print(f"🖼️ Switching to {mode} view mode")
    app.state.set_processing_mode(mode)
    # Update button states
    app.update_view_buttons()
    # Force immediate display update
    app.display_image()

