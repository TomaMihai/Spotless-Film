# Spotless UI helpers for SpotlessFilmModern

import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Optional, Tuple, List
from dust_removal_state import ToolMode  # <-- Add this import
import numpy as np

# All UI setup and update methods moved here from SpotlessFilmModern.
# Example: setup_ui, setup_modern_sidebar, create_macos_sidebar_content, create_collapsible_section, etc.

# --- UI Setup Methods ---
def setup_ui(self):
    """Setup the professional three-pane interface"""
    self.main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#1E1E1E")
    self.main_frame.pack(fill='both', expand=True)
    self.main_frame.grid_columnconfigure(1, weight=1)
    self.main_frame.grid_rowconfigure(0, weight=1)
    self.setup_modern_sidebar()
    self.setup_center_panel()
    self.setup_status_bar()
    self.state.add_observer(self.update_ui)

def setup_modern_sidebar(self):
    self.sidebar_frame = ctk.CTkFrame(self.main_frame, width=360, corner_radius=0, fg_color="#2A2A2A")
    self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
    self.sidebar_frame.grid_rowconfigure(4, weight=1)
    self.sidebar_frame.grid_propagate(False)
    self.create_macos_sidebar_content()

def create_macos_sidebar_content(self):
    header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
    title_label = ctk.CTkLabel(header_frame, text="✨ Dust Remover", font=ctk.CTkFont(size=18, weight="bold"))
    title_label.pack(anchor="w")
    subtitle_label = ctk.CTkLabel(header_frame, text="AI-powered film restoration", font=ctk.CTkFont(size=11), text_color="#888888")
    subtitle_label.pack(anchor="w", pady=(2, 0))
    self.create_collapsible_section("Import", 1, self.create_import_section)
    self.create_collapsible_section("Detection", 2, self.create_detection_section)
    self.create_collapsible_section("Dust Removal", 3, self.create_removal_section)

def create_collapsible_section(self, title, row, content_creator):
    section_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
    section_frame.grid(row=row, column=0, sticky="ew", padx=15, pady=(10, 0))
    header_btn = ctk.CTkButton(section_frame, text=f"▼ {title}", font=ctk.CTkFont(size=13, weight="bold"), fg_color="transparent", text_color="#CCCCCC", hover_color="#3A3A3A", anchor="w", height=30)
    header_btn.pack(fill="x")
    content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
    content_frame.pack(fill="x", pady=(5, 0))
    setattr(self, f"{title.lower().replace(' ', '_')}_content", content_frame)
    setattr(self, f"{title.lower().replace(' ', '_')}_expanded", True)
    content_creator(content_frame)
    def toggle_section():
        current_state = getattr(self, f"{title.lower().replace(' ', '_')}_expanded")
        new_state = not current_state
        setattr(self, f"{title.lower().replace(' ', '_')}_expanded", new_state)
        header_btn.configure(text=f"{'▼' if new_state else '▶'} {title}")
        if new_state:
            content_frame.pack(fill="x", pady=(5, 0))
        else:
            content_frame.pack_forget()
    header_btn.configure(command=toggle_section)

def create_import_section(self, parent):
    self.import_status_frame = ctk.CTkFrame(parent, fg_color="transparent")
    self.import_status_frame.pack(fill="x", pady=(0, 10))
    self.import_status_label = ctk.CTkLabel(self.import_status_frame, text="○ No image selected", font=ctk.CTkFont(size=12), text_color="#888888")
    self.import_status_label.pack(anchor="w")
    self.image_info_frame = ctk.CTkFrame(parent, fg_color="transparent")
    self.image_info_frame.pack(fill="x", pady=(0, 10))
    self.size_label = ctk.CTkLabel(self.image_info_frame, text="Size: --", font=ctk.CTkFont(size=10), text_color="#888888")
    self.size_label.pack(anchor="w")
    self.colorspace_label = ctk.CTkLabel(self.image_info_frame, text="Format: --", font=ctk.CTkFont(size=10), text_color="#888888")
    self.colorspace_label.pack(anchor="w")
    self.import_btn = ctk.CTkButton(parent, text="📁 Choose File", command=self.safe_import_image, font=ctk.CTkFont(size=12), height=32, fg_color="#4A4A4A", hover_color="#5A5A5A")
    self.import_btn.pack(fill="x", pady=(0, 5))
    self.batch_btn = ctk.CTkButton(parent, text="📂 Batch Process Folder", command=self.batch_process_folder_dialog, font=ctk.CTkFont(size=12), height=32, fg_color="#4A4A4A", hover_color="#5A5A5A")
    self.batch_btn.pack(fill="x", pady=(0, 5))
    # --- Batch Sensitivity Slider ---
    batch_sens_frame = ctk.CTkFrame(parent, fg_color="transparent")
    batch_sens_frame.pack(fill="x", pady=(0, 5))
    header_row = ctk.CTkFrame(batch_sens_frame, fg_color="transparent")
    header_row.pack(fill="x")
    batch_sens_label = ctk.CTkLabel(header_row, text="Batch Sensitivity", font=ctk.CTkFont(size=11, weight="bold"))
    batch_sens_label.pack(side="left")
    self.batch_threshold_value_label = ctk.CTkLabel(header_row, text=f"{getattr(self.state, 'batch_threshold', 0.2):.4f}", font=ctk.CTkFont(size=10), text_color="#CCCCCC")
    self.batch_threshold_value_label.pack(side="right")
    slider_frame = ctk.CTkFrame(batch_sens_frame, fg_color="transparent")
    slider_frame.pack(fill="x")
    less_label = ctk.CTkLabel(slider_frame, text="More Sensitive", font=ctk.CTkFont(size=9), text_color="#888888")
    less_label.pack(side="left")
    more_label = ctk.CTkLabel(slider_frame, text="Less Sensitive", font=ctk.CTkFont(size=9), text_color="#888888")
    more_label.pack(side="right")
    self.batch_threshold_slider = ctk.CTkSlider(
        slider_frame, from_=0.0001, to=0.2, number_of_steps=200,
        command=self.on_batch_threshold_changed
    )
    self.batch_threshold_slider.set(getattr(self.state, 'batch_threshold', 0.0750))
    self.batch_threshold_slider.pack(fill="x", pady=(5, 0))

def create_removal_section(self, parent):
    self.remove_btn = ctk.CTkButton(parent, text="?? Remove Dust", command=self.remove_dust, font=ctk.CTkFont(size=12), height=32, state="disabled", fg_color="#4A4A4A", hover_color="#5A5A5A")
    self.remove_btn.pack(fill="x", pady=(0, 10))
    self.processing_time_frame = ctk.CTkFrame(parent, fg_color="transparent")
    self.processing_time_frame.pack(fill="x")
    time_title = ctk.CTkLabel(self.processing_time_frame, text="Processing Time:", font=ctk.CTkFont(size=10), text_color="#888888")
    time_title.pack(anchor="w")
    self.processing_time_label = ctk.CTkLabel(self.processing_time_frame, text="0.00s", font=ctk.CTkFont(size=12), text_color="#CCCCCC")
    self.processing_time_label.pack(anchor="w")

def create_detection_section(self, parent):
    self.detect_btn = ctk.CTkButton(parent, text="🔍 Detect Dust", command=self.detect_dust, font=ctk.CTkFont(size=12), height=32, state="disabled", fg_color="#4A4A4A", hover_color="#5A5A5A")
    self.detect_btn.pack(fill="x", pady=(0, 15))
    self.threshold_frame = ctk.CTkFrame(parent, fg_color="transparent")
    self.threshold_frame.pack(fill="x", pady=(0, 0))
    header_row = ctk.CTkFrame(self.threshold_frame, fg_color="transparent")
    header_row.pack(fill="x")
    sensitivity_label = ctk.CTkLabel(header_row, text="🎯 Sensitivity", font=ctk.CTkFont(size=12, weight="bold"))
    sensitivity_label.pack(side="left")
    self.threshold_value_label = ctk.CTkLabel(header_row, text=f"{getattr(self.state.processing_state, 'threshold', 0.0750):.4f}", font=ctk.CTkFont(size=11), text_color="#CCCCCC")
    self.threshold_value_label.pack(side="right")
    slider_frame = ctk.CTkFrame(self.threshold_frame, fg_color="transparent")
    slider_frame.pack(fill="x", pady=(0, 5))
    labels_frame = ctk.CTkFrame(slider_frame, fg_color="transparent")
    labels_frame.pack(fill="x")
    less_label = ctk.CTkLabel(labels_frame, text="More Sensitive", font=ctk.CTkFont(size=9), text_color="#888888")
    less_label.pack(side="left")
    more_label = ctk.CTkLabel(labels_frame, text="Less Sensitive", font=ctk.CTkFont(size=9), text_color="#888888")
    more_label.pack(side="right")    
    self.threshold_slider = ctk.CTkSlider(slider_frame, from_=0.0001, to=0.2, command=self.on_threshold_changed, number_of_steps=200)
    self.threshold_slider.set(getattr(self.state.processing_state, 'threshold', 0.0750))
    self.threshold_slider.set(getattr(self.state, 'threshold', 0.0750))
    self.threshold_slider.pack(fill="x", pady=(5, 0))
    help_label = ctk.CTkLabel(self.threshold_frame, text="Lower values detect only strongest dust; raise for more.", font=ctk.CTkFont(size=9), text_color="#666666")
    help_label.pack(anchor="w", pady=(5, 0))

# --- Brush Cursor Methods ---
def on_mouse_motion(self, event):
    """Handle mouse motion for brush cursor"""
    if not self.use_gl and hasattr(self.state, 'view_state') and self.state.view_state.tool_mode in (ToolMode.BRUSH, ToolMode.ERASER):
        self.update_brush_cursor(event.x, event.y)
    else:
        self.hide_brush_cursor()
    
def update_brush_cursor(self, x, y):
    """Update brush cursor position and size"""
    if self.use_gl or not hasattr(self, 'canvas'):
        return  # Skip for OpenGL view or if canvas not ready
            
    # Hide old cursor
    if self.brush_cursor_id:
        try:
            self.canvas.delete(self.brush_cursor_id)
        except:
            pass
        
    # Get brush size (actual pixel size regardless of zoom)
    brush_size = getattr(self.state.view_state, 'brush_size', 20)
        
    # Scale brush size by current zoom level to show actual size on image
    zoom_scale = getattr(self.state.view_state, 'zoom_scale', 1.0)
    display_size = int(brush_size * zoom_scale)
        
    # Ensure minimum visibility (at least 4 pixels) and maximum reasonable size (200 pixels)
    display_size = max(4, min(200, display_size))
        
    # Create cursor circle
    x1 = x - display_size // 2
    y1 = y - display_size // 2
    x2 = x + display_size // 2
    y2 = y + display_size // 2
        
    # Red colors for both brush and eraser (Tkinter compatible colors)
    if self.state.view_state.tool_mode == ToolMode.BRUSH:
        outline_color = "#DC143C"  # Crimson red
        fill_color = "#FFB6C1"  # Light pink (low opacity effect)
    else:  # ERASER
        outline_color = "#B22222"  # Fire brick red
        fill_color = "#FFA0A0"  # Light red (low opacity effect)
        
    try:
        self.brush_cursor_id = self.canvas.create_oval(
            x1, y1, x2, y2,
            outline=outline_color, 
            fill=fill_color,
            width=2,
            dash=(5, 3),  # Dashed line for better visibility
            tags="brush_cursor"  # Add tag for easier management
        )
        self.cursor_visible = True
        print(f"Brush cursor created: {self.state.view_state.tool_mode}, size: {display_size}")
    except Exception as e:
        print(f"Error creating brush cursor: {e}")
    
def hide_brush_cursor(self):
    """Hide the brush cursor"""
    if not self.use_gl and hasattr(self, 'canvas'):
        try:
            # Delete by tag to ensure all cursor elements are removed
            self.canvas.delete("brush_cursor")
            if self.brush_cursor_id:
                self.canvas.delete(self.brush_cursor_id)
        except:
            pass
        self.brush_cursor_id = None
        self.cursor_visible = False
    
def update_cursor_for_tool_change(self):
    """Update cursor when tool mode changes"""
    if not self.use_gl and hasattr(self, 'canvas'):
        # Check if space is pressed - always prioritize panning cursor
        if hasattr(self.state, 'view_state') and self.state.view_state.space_key_pressed:
            try:
                self.canvas.config(cursor="fleur")  # Panning cursor (4-way arrow)
                print("Space pressed: panning cursor active")
            except:
                pass
            self.hide_brush_cursor()
        elif hasattr(self.state, 'view_state') and self.state.view_state.tool_mode in (ToolMode.BRUSH, ToolMode.ERASER):
            # Set custom cursor for tools (only when space is not pressed)
            try:
                self.canvas.config(cursor="none")  # Hide default cursor
                print(f"Tool activated: {self.state.view_state.tool_mode}, cursor hidden")
            except:
                pass
        else:
            # Reset to default cursor
            try:
                self.canvas.config(cursor="")
                print("Tool deactivated, cursor restored")
            except:
                pass
            self.hide_brush_cursor()

def on_batch_threshold_changed(self, value):
    self.batch_threshold_value_label.configure(text=f"{float(value):.4f}")
    self.state.batch_threshold = float(value)
