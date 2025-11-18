import customtkinter as ctk
from spotless_ui import (
    setup_ui as setup_ui_helper,
    setup_modern_sidebar as setup_modern_sidebar_helper,
    create_macos_sidebar_content as create_macos_sidebar_content_helper,
    create_collapsible_section as create_collapsible_section_helper,
    create_import_section as create_import_section_helper,
    create_detection_section as create_detection_section_helper,
    create_removal_section as create_removal_section_helper,
)

def setup_ui(app):
    setup_ui_helper(app)

def setup_modern_sidebar(app):
    setup_modern_sidebar_helper(app)

def create_macos_sidebar_content(app):
    create_macos_sidebar_content_helper(app)

def create_collapsible_section(app, parent, title, content_callback):
    return create_collapsible_section_helper(app, parent, title, content_callback)

def create_import_section(app, parent):
    create_import_section_helper(app, parent)

def create_detection_section(app, parent):
    create_detection_section_helper(app, parent)

def create_removal_section(app, parent):
    create_removal_section_helper(app, parent)

def setup_center_panel(app):
    """Setup the center panel with toolbar and professional canvas"""
    # Center frame
    app.center_frame = ctk.CTkFrame(app.main_frame, corner_radius=0, fg_color="#2A2A2A")
    app.center_frame.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
    app.center_frame.grid_columnconfigure(0, weight=1)
    app.center_frame.grid_rowconfigure(1, weight=1)
    
    # Professional toolbar (converted to CustomTkinter)
    setup_modern_toolbar(app)
    
    # Canvas area frame
    app.canvas_frame = ctk.CTkFrame(app.center_frame, corner_radius=0)
    app.canvas_frame.grid(row=1, column=0, sticky="nsew")
    app.canvas_frame.grid_columnconfigure(0, weight=1)
    app.canvas_frame.grid_rowconfigure(0, weight=1)  # Canvas row (expandable)
    app.canvas_frame.grid_rowconfigure(1, weight=0)  # Zoom controls row (fixed height)
    
    # Simple CustomTkinter canvas
    canvas_container = ctk.CTkFrame(app.canvas_frame, fg_color="transparent")
    canvas_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    canvas_container.grid_columnconfigure(0, weight=1)
    canvas_container.grid_rowconfigure(0, weight=1)
    
    # Force reliable Tk canvas path on macOS; disable GL to avoid circular import issues
    app.use_gl = False
    # Create simple canvas for image display (darker background to match macOS)
    app.canvas = ctk.CTkCanvas(canvas_container, bg="#1E1E1E", highlightthickness=0)
    app.canvas.grid(row=0, column=0, sticky="nsew")
    
    # Bind canvas events
    if not app.use_gl:
        app.canvas.bind('<Configure>', app.on_canvas_resize)
        app.canvas.bind('<Button-1>', app.on_canvas_click)
        app.canvas.bind('<B1-Motion>', app.on_canvas_drag)
        app.canvas.bind('<ButtonRelease-1>', app.on_canvas_release)
        app.canvas.bind('<MouseWheel>', app.on_mouse_wheel)
        app.canvas.bind('<Button-4>', app.on_mouse_wheel)  # Linux scroll up
        app.canvas.bind('<Button-5>', app.on_mouse_wheel)  # Linux scroll down
        app.canvas.bind('<Motion>', app.on_mouse_motion)  # For brush cursor
    
    # Initialize zoom/pan state (kept in central state)
    app.is_panning = False
    app.last_mouse_pos = None
    app.last_loaded_path = None  # Track loaded file for export
    if not app.use_gl:
        app.canvas.focus_set()  # Allow canvas to receive key events
    
    # Brush cursor state
    app.brush_cursor_id = None
    app.cursor_visible = False
    
    # Throttle/quality controls for zoom rendering on Tk canvas
    app._zoom_redraw_job = None
    app._zoom_finalize_delay_ms = 120
    app._current_resample = None  # None => high quality (LANCZOS); otherwise temporary
    
    # Canvas item handles for fast pan
    app.image_item_id = None
    app.overlay_item_id = None
    
    # Show welcome message or GL clear
    if not app.use_gl:
        app.show_welcome_message()
    
    # Add zoom controls under the canvas
    setup_zoom_controls_under_canvas(app)

def setup_zoom_controls_under_canvas(app):
    """Setup zoom controls under the canvas"""
    # Zoom controls frame under the canvas
    zoom_frame = ctk.CTkFrame(app.canvas_frame, height=50, corner_radius=8, 
                             fg_color="#3A3A3A")
    zoom_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
    zoom_frame.grid_propagate(False)
    
    # Center the zoom controls
    controls_container = ctk.CTkFrame(zoom_frame, fg_color="transparent")
    controls_container.pack(expand=True)
    
    # Zoom out button
    app.zoom_out_btn = ctk.CTkButton(controls_container, text="−", width=35, height=35,
                                     command=app.zoom_out,
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     fg_color="#5A5A5A", hover_color="#6A6A6A")
    app.zoom_out_btn.pack(side="left", padx=5)
    
    # Zoom percentage display
    app.zoom_label = ctk.CTkLabel(controls_container, text="100%", width=60,
                                  font=ctk.CTkFont(size=12, family="Monaco"))
    app.zoom_label.pack(side="left", padx=5)
    
    # Zoom in button
    app.zoom_in_btn = ctk.CTkButton(controls_container, text="+", width=35, height=35,
                                    command=app.zoom_in,
                                    font=ctk.CTkFont(size=16, weight="bold"),
                                    fg_color="#5A5A5A", hover_color="#6A6A6A")
    app.zoom_in_btn.pack(side="left", padx=5)
    
    # Reset zoom button
    app.reset_zoom_btn = ctk.CTkButton(controls_container, text="⌂", width=35, height=35,
                                       command=app.reset_zoom,
                                       font=ctk.CTkFont(size=14),
                                       fg_color="#5A5A5A", hover_color="#6A6A6A")
    app.reset_zoom_btn.pack(side="left", padx=(10, 5))

def setup_modern_toolbar(app):
    """Setup macOS-style toolbar with proper tools and overlay controls"""
    toolbar_frame = ctk.CTkFrame(app.center_frame, height=60, corner_radius=0, 
                                fg_color="#3A3A3A")
    toolbar_frame.grid(row=0, column=0, sticky="ew", pady=(0, 1))
    toolbar_frame.grid_columnconfigure(1, weight=1)
    toolbar_frame.grid_propagate(False)
    
    # Left side tools (matching macOS layout)
    left_tools_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
    left_tools_frame.grid(row=0, column=0, sticky="w", padx=20, pady=10)
    
    # Eraser button (square style)
    app.eraser_btn = ctk.CTkButton(left_tools_frame, text="⬜\nEraser", width=80, height=50,
                                   command=app.toggle_eraser_tool,
                                   font=ctk.CTkFont(size=10),
                                   fg_color="#5A5A5A", hover_color="#6A6A6A")
    app.eraser_btn.pack(side="left", padx=(0, 8))
    
    # Brush button (square style)
    app.brush_btn = ctk.CTkButton(left_tools_frame, text="⬛\nBrush", width=80, height=50,
                                 command=app.toggle_brush_tool,
                                 font=ctk.CTkFont(size=10),
                                 fg_color="#5A5A5A", hover_color="#6A6A6A")
    app.brush_btn.pack(side="left", padx=(0, 8))
    
    # Brush size controls (conditional - only show when brush/eraser active)
    app.brush_size_frame = ctk.CTkFrame(left_tools_frame, fg_color="transparent")
    
    app.brush_size_label_text = ctk.CTkLabel(app.brush_size_frame, text="Size:", 
                                             font=ctk.CTkFont(size=11), text_color="#CCCCCC")
    app.brush_size_label_text.pack(side="left")
    
    app.brush_size_slider = ctk.CTkSlider(app.brush_size_frame, from_=5, to=100, width=120,
                                          command=app.on_brush_size_changed)
    app.brush_size_slider.set(10)  # Initialize to default brush size
    app.brush_size_slider.pack(side="left", padx=(8, 8))
    
    app.brush_size_value_label = ctk.CTkLabel(app.brush_size_frame, text="10px", width=40,
                                              font=ctk.CTkFont(size=11, family="Monaco"), 
                                              text_color="#CCCCCC")
    app.brush_size_value_label.pack(side="left")
    
    # Pack brush size frame initially for testing
    app.brush_size_frame.pack(side="left", padx=(20, 0))
    
    
    # Center view mode button (single cycling button)
    center_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
    center_frame.grid(row=0, column=1, pady=10)
    
    # Single cycling view mode button
    app.view_cycle_btn = ctk.CTkButton(center_frame, text="🔍 Single", width=120, height=35,
                                       command=app.cycle_view_mode,
                                       font=ctk.CTkFont(size=12),
                                       fg_color="#007AFF", hover_color="#0051D0")
    app.view_cycle_btn.pack(side="left", padx=2)
    
    # Right side overlay controls
    right_controls_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
    right_controls_frame.grid(row=0, column=2, sticky="e", padx=20, pady=10)
    
    # Overlay toggle and controls
    overlay_frame = ctk.CTkFrame(right_controls_frame, fg_color="transparent")
    overlay_frame.pack(side="right")
    
    # Timer display (matching macOS)
    app.timer_label = ctk.CTkLabel(overlay_frame, text="⏱ 2.47s",
                                   font=ctk.CTkFont(size=12), text_color="#CCCCCC")
    app.timer_label.pack(side="right", padx=(0, 20))
    
    # Export button
    app.export_btn = ctk.CTkButton(overlay_frame, text="💾 Export", width=80, height=35,
                                   command=app.export_full_resolution,
                                   font=ctk.CTkFont(size=11),
                                   fg_color="#28A745", hover_color="#1E7E34")
    app.export_btn.pack(side="right", padx=(0, 10))
    
    # Overlay toggle button
    app.overlay_toggle_btn = ctk.CTkButton(overlay_frame, text="👁 Overlay", width=80, height=35,
                                          command=app.toggle_overlay,
                                          font=ctk.CTkFont(size=11),
                                          fg_color="#007AFF", hover_color="#0051D0")
    app.overlay_toggle_btn.pack(side="right", padx=(0, 10))
    
    # Opacity section
    opacity_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
    opacity_frame.pack(side="right", padx=(0, 10))
    
    opacity_label = ctk.CTkLabel(opacity_frame, text="Opacity",
                                font=ctk.CTkFont(size=10), text_color="#888888")
    opacity_label.pack()
    
    # Opacity slider frame
    opacity_slider_frame = ctk.CTkFrame(opacity_frame, fg_color="transparent")
    opacity_slider_frame.pack(fill="x")
    
    # Opacity slider (matching macOS design)
    app.opacity_slider = ctk.CTkSlider(opacity_slider_frame, from_=0.0, to=1.0,
                                       command=app.on_opacity_changed,
                                       number_of_steps=20, width=100)
    app.opacity_slider.set(0.5)  # 50% default
    app.opacity_slider.pack(side="left")
    
    # Opacity percentage
    app.opacity_label = ctk.CTkLabel(opacity_slider_frame, text="50%",
                                     font=ctk.CTkFont(size=10), text_color="#CCCCCC")
    app.opacity_label.pack(side="right", padx=(5, 0))
    
    # Initialize overlay state
    app.overlay_visible = True
    app.overlay_opacity = 0.5  # 50% default
    
    # Initialize brush size
    app.state.view_state.brush_size = 10
    
    # Initialize zoom UI to 100%
    app.update_zoom_ui()

def setup_status_bar(app):
    """Setup modern status bar"""
    app.status_frame = ctk.CTkFrame(app.main_frame, height=30, corner_radius=0)
    app.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
    app.status_frame.grid_columnconfigure(1, weight=1)
    app.status_frame.grid_propagate(False)
    
    # Device info
    device_text = f"Device: {app.state.device}"
    app.device_label = ctk.CTkLabel(app.status_frame, text=device_text,
                                    font=ctk.CTkFont(size=10), text_color="gray60")
    app.device_label.grid(row=0, column=0, sticky="w", padx=10)
    
    # Status message
    app.status_label = ctk.CTkLabel(app.status_frame, text="Ready - Import an image to begin",
                                    font=ctk.CTkFont(size=10), text_color="gray70")
    app.status_label.grid(row=0, column=1, sticky="w", padx=10)
    
    # LaMa status
    app.lama_label = ctk.CTkLabel(app.status_frame, text="LaMa: Loading...",
                                  font=ctk.CTkFont(size=10), text_color="gray60")
    app.lama_label.grid(row=0, column=2, sticky="e", padx=10)

def show_welcome_message(app):
    """Show welcome message on canvas"""
    app.canvas.delete('all')
    canvas_width = app.canvas.winfo_width() or 800
    canvas_height = app.canvas.winfo_height() or 600
    
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    
    # Welcome text with modern styling
    app.canvas.create_text(center_x, center_y - 60, text="✨",
                           font=("Helvetica", 64), fill="#4a9eff")
    app.canvas.create_text(center_x, center_y, text="Spotless Film",
                           font=("Helvetica", 24, "bold"), fill="white")
    app.canvas.create_text(center_x, center_y + 35, text="Drag and drop an image here to begin",
                           font=("Helvetica", 14), fill="gray")
    app.canvas.create_text(center_x, center_y + 65, text="or use the Import button",
                           font=("Helvetica", 12), fill="gray")
    app.canvas.create_text(center_x, center_y + 95, text="Supported formats: PNG, JPEG, TIFF, BMP",
                           font=("Helvetica", 10), fill="#666666")

def update_ui(app):
    """Update UI based on state changes"""
    # Keep zoom UI in sync with state changes
    app.update_zoom_ui()
    # Update button states
    has_image = app.state.selected_image is not None
    has_dust_mask = app.state.dust_mask is not None
    has_processed = app.state.processed_image is not None
    has_prediction = app.state.raw_prediction_mask is not None
    
    # Update button states
    if hasattr(app, 'detect_btn'):
        app.detect_btn.configure(state="normal" if has_image and not app.state.processing_state.is_detecting else "disabled")
    if hasattr(app, 'remove_btn'):
        app.remove_btn.configure(state="normal" if has_dust_mask and not app.state.processing_state.is_removing else "disabled")
    if hasattr(app, 'export_btn'):
        app.export_btn.configure(state="normal" if has_processed else "disabled")
    
    # Show/Hide threshold slider (matches Swift app behavior)
    if hasattr(app, 'threshold_frame'):
        if has_prediction:
            app.threshold_frame.pack(fill="x", padx=15, pady=(0, 15))
        else:
            app.threshold_frame.pack_forget()
    
    # Update import status and image info (keep elements visible to prevent layout shifts)
    if hasattr(app, 'import_status_label'):
        if has_image:
            app.import_status_label.configure(text="● Image Loaded", text_color="#4CAF50")
            # Update image info
            if hasattr(app, 'size_label') and app.state.selected_image:
                size = app.state.selected_image.size
                app.size_label.configure(text=f"Size: {size[0]} x {size[1]}")
            if hasattr(app, 'colorspace_label'):
                mode = getattr(app.state.selected_image, 'mode', 'RGB')
                app.colorspace_label.configure(text=f"Format: {mode}")
        else:
            app.import_status_label.configure(text="○ No image selected", text_color="#888888")
            if hasattr(app, 'size_label'):
                app.size_label.configure(text="Size: --")
            if hasattr(app, 'colorspace_label'):
                app.colorspace_label.configure(text="Format: --")
    
    # Update processing time
    if hasattr(app, 'processing_time_label') and hasattr(app.state.processing_state, 'processing_time'):
        if app.state.processing_state.processing_time > 0:
            time_text = f"{app.state.processing_state.processing_time:.2f}s"
            app.processing_time_label.configure(text=time_text)
    
    # Update toolbar timer
    if hasattr(app, 'timer_label') and hasattr(app.state.processing_state, 'processing_time'):
        if app.state.processing_state.processing_time > 0:
            time_text = f"⏱ {app.state.processing_state.processing_time:.2f}s"
            app.timer_label.configure(text=time_text)
    
    # Show/Hide export section  
    if hasattr(app, 'export_frame'):
        if has_processed:
            app.export_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 15))
        else:
            app.export_frame.grid_forget()
    
    # Update toolbar button states if they exist
    if hasattr(app, 'view_cycle_btn'):
        app.update_tool_buttons()
    
    # Display current image
    if app.state.selected_image:
        app.display_image()
    
    # Update processing button text
    if hasattr(app, 'detect_btn'):
        if app.state.processing_state.is_detecting:
            app.detect_btn.configure(text="🔍  Detecting...")
        else:
            app.detect_btn.configure(text="🔍  Detect Dust")
    
    if hasattr(app, 'remove_btn'):        
        if app.state.processing_state.is_removing:
            app.remove_btn.configure(text="✨  Removing...")
        else:
            app.remove_btn.configure(text="✨  Remove Dust")