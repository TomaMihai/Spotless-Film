
import os
from tkinter import filedialog, messagebox
from PIL import Image

def safe_import_image(app):
    """Safe wrapper for import_image to prevent multiple dialogs"""
    if app._importing:
        print("🔵 Import already in progress, ignoring click")
        return
    
    app._importing = True
    app.import_btn.configure(text="📁  Loading...", state="disabled")
    
    try:
        import_image(app)
    finally:
        app._importing = False
        app.import_btn.configure(text="📁  Choose Image", state="normal")

def import_image(app):
    """Import an image file"""
    print("🔵 Import image button clicked")
    try:
        print("🔵 Opening file dialog...")
        file_path = filedialog.askopenfilename(
            title="Select Image",
            initialdir=os.path.expanduser("~"),  # Start in home directory
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.tiff *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("TIFF files", "*.tiff *.tif"),
                ("All files", "*.*")
            ]
        )
        
        print(f"🔵 File dialog returned: '{file_path}' (type: {type(file_path)})")
        
        if file_path and file_path.strip():  # Check for valid path
            print(f"🔵 Valid file path, loading: {file_path}")
            load_image(app, file_path)
        else:
            print("🔵 No file selected or empty path")
            
    except Exception as e:
        print(f"❌ Error in import_image: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to open file dialog: {str(e)}")

def load_image(app, file_path: str):
    """Load image from file path"""
    print(f"🔵 Loading image: {file_path}")
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load image
        image = Image.open(file_path)
        app.state.selected_image = image
        # Store the file path for export functionality
        app.last_loaded_path = file_path
        # Build preview version for faster display
        app.preview_selected_image = app.build_preview_image(image)
        app.state.reset_processing()
        
        filename = os.path.basename(file_path)
        print(f"✅ Image loaded: {filename} ({image.size[0]}x{image.size[1]})")
        print(f"✅ State.selected_image set: {app.state.selected_image is not None}")
        print(f"✅ Can detect dust now: {app.state.can_detect_dust}")
        
        # Update UI
        app.status_label.configure(text=f"Image loaded: {filename}")
        
        # Enable detect button
        if hasattr(app, 'detect_btn'):
            app.detect_btn.configure(state="normal")
        
        # Update canvas display
        app.update_ui()
        
    except Exception as e:
        error_msg = f"Failed to load image: {str(e)}"
        print(f"❌ {error_msg}")
        app.status_label.configure(text=error_msg, text_color="red")
        messagebox.showerror("Error", error_msg)

def handle_file_drop(app, files: list[str]):
    """Handle drag and drop files"""
    if not files:
        return
    
    file_path = files[0]
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp')):
        load_image(app, file_path)
    else:
        messagebox.showerror("Error", "Please drop a valid image file")

def export_image(app):
    """Export processed image"""
    if not app.state.processed_image:
        messagebox.showwarning("Warning", "No processed image to export")
        return
    
    file_path = filedialog.asksaveasfilename(
        title="Save Processed Image",
        defaultextension=".png",
        filetypes=[
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("TIFF files", "*.tiff"),
            ("All files", "*.*")
        ]
    )
    
    if file_path:
        try:
            # Save with high quality
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                app.state.processed_image.save(file_path, 'JPEG', quality=95)
            else:
                app.state.processed_image.save(file_path)
            
            filename = os.path.basename(file_path)
            print(f"✅ Image saved: {filename}")
            app.status_label.configure(text=f"Image saved: {filename}")
            
            # Show in file manager
            if os.name == 'nt':  # Windows
                os.startfile(os.path.dirname(file_path))
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{os.path.dirname(file_path)}"')
                
        except Exception as e:
            app.state.show_error(f"Failed to save image: {str(e)}")

def export_full_resolution(app):
    """Export the full resolution processed image"""
    if not app.state.processed_image:
        messagebox.showwarning("Export Warning", "No processed image to export. Please process an image first.")
        return
    
    try:
        # Get the original filename to create export filename
        if hasattr(app, 'last_loaded_path') and app.last_loaded_path:
            import os
            base_name = os.path.splitext(os.path.basename(app.last_loaded_path))[0]
            default_name = f"{base_name}_dust_removed.jpg"
        else:
            default_name = "dust_removed_image.jpg"
        
        # Ask user for save location
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            initialfile=default_name,
            filetypes=[
                ("JPEG files", "*.jpg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ],
            title="Export Full Resolution Image"
        )
        
        if file_path:
            # Save the full resolution processed image
            app.state.processed_image.save(file_path, quality=95)
            messagebox.showinfo("Export Successful", f"Image exported successfully to:\n{file_path}")
            print(f"✅ Full resolution image exported: {file_path}")
        else:
            print("Export cancelled by user")
            
    except Exception as e:
        error_msg = f"Failed to export image: {str(e)}"
        messagebox.showerror("Export Error", error_msg)
        print(f"❌ Export error: {e}")
