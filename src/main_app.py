#!/usr/bin/env python3
"""
Spotless Film - Modern Professional Version

Main application entry point.
"""

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from pathlib import Path
import sys
from typing import Optional, List, Tuple
from PIL import Image
import threading

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# ---------------------------------------------------------------------------
# HuggingFace hub compatibility shim: newer versions removed cached_download.
# Some third-party dependencies (e.g. lama-cleaner) still import cached_download.
# Provide a fallback using hf_hub_download to prevent ImportError.
# ---------------------------------------------------------------------------
try:
    import huggingface_hub as _hf
    if not hasattr(_hf, "cached_download"):
        from huggingface_hub import hf_hub_download as _hf_hub_download
        def cached_download(*args, **kwargs):  # type: ignore
            return _hf_hub_download(*args, **kwargs)
        _hf.cached_download = cached_download  # type: ignore
except Exception:
    # If huggingface_hub itself is missing we leave it; later code will handle model availability.
    pass

from dust_removal_state import DustRemovalState, ProcessingMode, ToolMode
from ui_components import SpotlessSidebar, SpotlessToolbar, ZoomControls
from professional_canvas import SpotlessCanvas
from image_processing import ImageProcessingService, LamaInpainter, BrushTools, ProcessingTask, UNet
from simple_modern_theme import SimpleModernTheme
try:
    from gl_image_view import GLImageView, OPENGL_AVAILABLE, GL_IMPORT_ERROR
except Exception as e:
    OPENGL_AVAILABLE = False
    GL_IMPORT_ERROR = str(e)

# Import UI and batch helpers
import ui_setup
import canvas_event_handlers
import image_display
import file_operations
import processing_operations
import state_and_model_management
import ui_callbacks
import spotless_batch

# Set appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SpotlessFilmModern:
    """Modern professional Spotless Film application with macOS-style UI"""
    
    def __init__(self):
        # Create main window with drag-and-drop support
        self.root = TkinterDnD.Tk()
        self.root.title("✨ Spotless Film - AI-Powered Film Restoration")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Initialize state
        self.state = DustRemovalState(self.root)
        # Preview (downscaled) images for faster display
        self.preview_selected_image = None
        self.preview_processed_image = None
        # Split view caches
        self._split_cached_size = None
        self._split_resized_original = None
        self._split_resized_processed = None
        self._split_cached_signature = None
        
        # Initialize split view position
        self.split_position = 0.5  # Default to middle
        
        # Apply professional theme (skip for CustomTkinter compatibility)
        # self.theme = SimpleModernTheme(self.root)
        
        # Processing components
        self.lama_inpainter: Optional[LamaInpainter] = None
        self.processing_task: Optional[ProcessingTask] = None
        
        # Flags
        self._importing = False
        self._batch_running = False
        
        # Callback dictionary for UI components
        self.callbacks = {
            'import_image': self.import_image,
            'detect_dust': self.detect_dust,
            'remove_dust': self.remove_dust,
            'export_image': self.export_image,
            'threshold_changed': self.on_threshold_changed,
            'handle_drop': self.handle_file_drop,
            'eraser_click': self.apply_eraser_at_point,
            'brush_click': self.apply_brush_at_point
        }
        
        # Setup UI (now from spotless_ui)
        ui_setup.setup_ui(self)
        
        # Load models
        state_and_model_management.load_models_async(self)
        
        # Setup keyboard shortcuts
        ui_callbacks.setup_keyboard_shortcuts(self)
        
        print("✨ Spotless Film (Modern Professional) initialized")
    
    # UI methods now delegated to ui_setup
    def setup_ui(self):
        ui_setup.setup_ui(self)
    def setup_modern_sidebar(self):
        ui_setup.setup_modern_sidebar(self)
    def create_macos_sidebar_content(self):
        ui_setup.create_macos_sidebar_content(self)
    def create_collapsible_section(self, parent, title, content_callback):
        return ui_setup.create_collapsible_section(self, parent, title, content_callback)
    def create_import_section(self, parent):
        ui_setup.create_import_section(self, parent)
    def create_detection_section(self, parent):
        ui_setup.create_detection_section(self, parent)
    def create_removal_section(self, parent):
        ui_setup.create_removal_section(self, parent)
    def setup_center_panel(self):
        ui_setup.setup_center_panel(self)
    def setup_zoom_controls_under_canvas(self):
        ui_setup.setup_zoom_controls_under_canvas(self)
    def setup_modern_toolbar(self):
        ui_setup.setup_modern_toolbar(self)
    def setup_status_bar(self):
        ui_setup.setup_status_bar(self)
    def show_welcome_message(self):
        ui_setup.show_welcome_message(self)
    def update_ui(self):
        ui_setup.update_ui(self)

    # Canvas event handlers
    def on_canvas_resize(self, event):
        canvas_event_handlers.on_canvas_resize(self, event)
    def on_canvas_click(self, event):
        canvas_event_handlers.on_canvas_click(self, event)
    def on_canvas_drag(self, event):
        canvas_event_handlers.on_canvas_drag(self, event)
    def on_mouse_wheel(self, event):
        canvas_event_handlers.on_mouse_wheel(self, event)
    def on_canvas_release(self, event):
        canvas_event_handlers.on_canvas_release(self, event)
    def apply_eraser_at_point(self, point, canvas_width, canvas_height):
        canvas_event_handlers.apply_eraser_at_point(self, point, canvas_width, canvas_height)
    def apply_brush_at_point(self, point, canvas_width, canvas_height):
        canvas_event_handlers.apply_brush_at_point(self, point, canvas_width, canvas_height)

    # Image display
    def display_image(self, image=None):
        image_display.display_image(self, image)
    def display_single_view(self, canvas_width, canvas_height, image=None):
        image_display.display_single_view(self, canvas_width, canvas_height, image)
    def display_side_by_side_view(self, canvas_width, canvas_height):
        image_display.display_side_by_side_view(self, canvas_width, canvas_height)
    def display_split_view(self, canvas_width, canvas_height):
        image_display.display_split_view(self, canvas_width, canvas_height)
    def _get_split_bounds(self, canvas_width: int, canvas_height: int):
        return image_display._get_split_bounds(self, canvas_width, canvas_height)
    def display_single_view_gl(self, canvas_width, canvas_height):
        image_display.display_single_view_gl(self, canvas_width, canvas_height)
    def create_overlay_image(self, base_image):
        return image_display.create_overlay_image(self, base_image)
    def create_overlay_layer(self, display_size):
        return image_display.create_overlay_layer(self, display_size)
    def build_preview_image(self, image, long_side: int = 2048):
        return image_display.build_preview_image(self, image, long_side)

    # File operations
    def safe_import_image(self):
        file_operations.safe_import_image(self)
    def import_image(self):
        file_operations.import_image(self)
    def load_image(self, file_path: str):
        file_operations.load_image(self, file_path)
    def handle_file_drop(self, files: List[str]):
        file_operations.handle_file_drop(self, files)
    def export_image(self):
        file_operations.export_image(self)
    def export_full_resolution(self):
        file_operations.export_full_resolution(self)

    # Processing operations
    def detect_dust(self):
        processing_operations.detect_dust(self)
    def remove_dust(self):
        processing_operations.remove_dust(self)
    def perform_dust_removal(self) -> Image.Image:
        return processing_operations.perform_dust_removal(self)
    def perform_cv2_inpainting(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        return processing_operations.perform_cv2_inpainting(self, image, mask)

    # State and model management
    def load_models_async(self):
        state_and_model_management.load_models_async(self)
    def find_model_files(self) -> dict:
        return state_and_model_management.find_model_files(self)
    def handle_processing_error(self, error: Exception, operation: str):
        state_and_model_management.handle_processing_error(self, error, operation)
    def update_dust_mask_with_threshold(self):
        state_and_model_management.update_dust_mask_with_threshold(self)
    def update_dust_mask_with_threshold_realtime(self):
        state_and_model_management.update_dust_mask_with_threshold_realtime(self)

    # UI callbacks
    def on_mouse_motion(self, event):
        ui_callbacks.on_mouse_motion(self, event)
    def update_brush_cursor(self):
        ui_callbacks.update_brush_cursor(self)
    def hide_brush_cursor(self):
        ui_callbacks.hide_brush_cursor(self)
    def update_cursor_for_tool_change(self):
        ui_callbacks.update_cursor_for_tool_change(self)
    def cycle_view_mode(self):
        ui_callbacks.cycle_view_mode(self)
    def toggle_eraser_tool(self):
        ui_callbacks.toggle_eraser_tool(self)
    def toggle_brush_tool(self):
        ui_callbacks.toggle_brush_tool(self)
    def on_brush_size_changed(self, value):
        ui_callbacks.on_brush_size_changed(self, value)
    def toggle_overlay(self):
        ui_callbacks.toggle_overlay(self)
    def on_opacity_changed(self, value):
        ui_callbacks.on_opacity_changed(self, value)
    def zoom_in(self):
        ui_callbacks.zoom_in(self)
    def zoom_out(self):
        ui_callbacks.zoom_out(self)
    def reset_zoom(self):
        ui_callbacks.reset_zoom(self)
    def update_zoom_ui(self):
        ui_callbacks.update_zoom_ui(self)
    def update_tool_buttons(self):
        ui_callbacks.update_tool_buttons(self)
    def setup_keyboard_shortcuts(self):
        ui_callbacks.setup_keyboard_shortcuts(self)
    def toggle_dust_overlay(self):
        ui_callbacks.toggle_dust_overlay(self)
    def toggle_space_mode(self, pressed: bool):
        ui_callbacks.toggle_space_mode(self, pressed)
    def toggle_compare_mode(self):
        ui_callbacks.toggle_compare_mode(self)
    def undo_mask_change(self):
        ui_callbacks.undo_mask_change(self)
    def on_threshold_changed(self, value):
        ui_callbacks.on_threshold_changed(self, value)
    def set_view_mode(self, mode: ProcessingMode):
        ui_callbacks.set_view_mode(self, mode)

    # Batch processing
    def _show_messagebox_async(self, kind: str, title: str, msg: str):
        spotless_batch._show_messagebox_async(self, kind, title, msg)
    def _update_status_async(self, text: str, color: Optional[str] = None):
        spotless_batch._update_status_async(self, text, color)
    def _finish_batch_ui(self, progress_window=None):
        spotless_batch._finish_batch_ui(self, progress_window)
    def batch_process_folder_dialog(self):
        spotless_batch.batch_process_folder_dialog(self)
    def _batch_process_folder_worker(self, root_folder: str, progress_window, stop_event: threading.Event):
        spotless_batch._batch_process_folder_worker(self, root_folder, progress_window, stop_event)

    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SpotlessFilmModern()
    app.run()