# Spotless batch processing helpers for SpotlessFilmModern
from tkinter import messagebox, filedialog
from typing import Optional, List
import threading
import threading
import os
import time
from PIL import Image
import numpy as np
import customtkinter as ctk

from image_processing import ImageProcessingService

class BatchProgressWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Batch Processing Progress")
        self.geometry("400x250")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_closing) # Handle window close button

        self.stop_event = threading.Event() # Event to signal batch process to stop

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # For the main frame

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Initializing batch...", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.total_files_label = ctk.CTkLabel(self.main_frame, text="Total files: 0")
        self.total_files_label.grid(row=2, column=0, pady=(5, 2), sticky="w", padx=20)

        self.skipped_files_label = ctk.CTkLabel(self.main_frame, text="Skipped files: 0")
        self.skipped_files_label.grid(row=3, column=0, pady=2, sticky="w", padx=20)

        self.processed_files_label = ctk.CTkLabel(self.main_frame, text="Processed: 0")
        self.processed_files_label.grid(row=4, column=0, pady=2, sticky="w", padx=20)
        
        self.remaining_files_label = ctk.CTkLabel(self.main_frame, text="Remaining: 0")
        self.remaining_files_label.grid(row=5, column=0, pady=2, sticky="w", padx=20)

        self.eta_label = ctk.CTkLabel(self.main_frame, text="ETA: Calculating...")
        self.eta_label.grid(row=6, column=0, pady=(5, 10), sticky="w", padx=20)

        self.close_button = ctk.CTkButton(self.main_frame, text="Close", command=self.destroy, state="disabled")
        self.close_button.grid(row=7, column=0, pady=(10, 10))

        self.update_idletasks() # Ensure window is drawn

        # Center the window
        master_x = master.winfo_x()
        master_y = master.winfo_y()
        master_width = master.winfo_width()
        master_height = master.winfo_height()

        self_width = self.winfo_width()
        self_height = self.winfo_height()

        x = master_x + (master_width // 2) - (self_width // 2)
        y = master_y + (master_height // 2) - (self_height // 2)

        self.geometry(f"+{x}+{y}")

    def update_progress(self, processed: int, total: int, skipped: int, eta_seconds: Optional[float] = None):
        self.status_label.configure(text=f"Processing file {processed}/{total}...")
        self.progress_bar.set(processed / total if total > 0 else 0)
        self.total_files_label.configure(text=f"Total files: {total}")
        self.skipped_files_label.configure(text=f"Skipped files: {skipped}")
        self.processed_files_label.configure(text=f"Processed: {processed}")
        self.remaining_files_label.configure(text=f"Remaining: {total - processed - skipped}")

        if eta_seconds is not None:
            if eta_seconds < 60:
                self.eta_label.configure(text=f"ETA: {eta_seconds:.1f} seconds")
            else:
                minutes = int(eta_seconds // 60)
                seconds = int(eta_seconds % 60)
                self.eta_label.configure(text=f"ETA: {minutes}m {seconds}s")
        else:
            self.eta_label.configure(text="ETA: Calculating...")
        
        self.update_idletasks()

    def complete(self, processed: int, total: int, failed: int):
        self.status_label.configure(text=f"Batch complete! {processed} succeeded, {failed} failed.")
        self.progress_bar.set(1.0)
        self.eta_label.configure(text="ETA: Complete")
        self.close_button.configure(state="normal")
        self.update_idletasks()

    def _on_closing(self):
        """Handle window close button click."""
        print("Batch cancel requested, signaling worker thread...")
        self.status_label.configure(text="Cancelling...")
        self.stop_event.set()
        self.withdraw() # Hide the window immediately

def _show_messagebox_async(self, kind: str, title: str, msg: str):
    def _do():
        try:
            if kind == 'error':
                messagebox.showerror(title, msg)
            elif kind == 'info':
                messagebox.showinfo(title, msg)
            else:
                messagebox.showwarning(title, msg)
        except Exception:
            pass
    self.root.after_idle(_do)

def _update_status_async(self, text: str, color: Optional[str] = None):
    def _do():
        try:
            if color is not None:
                self.status_label.configure(text=text, text_color=color)
            else:
                self.status_label.configure(text=text)
        except Exception:
            pass
    self.root.after_idle(_do)

def _finish_batch_ui(self, progress_window=None):
    def _do():
        try:
            self.batch_btn.configure(text="✨ Batch Process Folder", state="normal")
            if progress_window and progress_window.winfo_exists():
                progress_window.destroy()
        except Exception:
            pass
        self._batch_running = False
    self.root.after_idle(_do)

def batch_process_folder_dialog(self):
    """Open a folder picker and start recursive batch processing in background."""
    if self._batch_running:
        return
    folder = filedialog.askdirectory(title="Select Folder to Batch Process")
    if not folder:
        return
    self._batch_running = True
    try:
        self.batch_btn.configure(text="Processing...", state="disabled")
    except Exception:
        pass
    
    progress_window = BatchProgressWindow(self.root)
    self.root.attributes('-alpha', 1.0) # Force main window to be opaque
    
    t = threading.Thread(target=self._batch_process_folder_worker, args=(folder, progress_window, progress_window.stop_event))
    t.daemon = True
    t.start()

def _batch_process_folder_worker(self, root_folder: str, progress_window, stop_event: threading.Event):
    try:
        # Ensure model is available
        if not self.state.unet_model:
            self._update_status_async("Model not loaded. Please wait for models to load.", "red")
            self._show_messagebox_async('error', 'Batch Error', 'U-Net model not loaded. Please wait for models to load.')
            self.root.after_idle(lambda: progress_window.destroy())
            return

        supported_ext = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")
        all_files: List[str] = []
        for dirpath, _dirnames, filenames in os.walk(root_folder):
            for fname in filenames:
                if fname.lower().endswith(supported_ext):
                    all_files.append(os.path.join(dirpath, fname))

        total_potential_files = len(all_files)
        if total_potential_files == 0:
            self._update_status_async("No images found in selected folder.")
            self.root.after_idle(lambda: progress_window.destroy())
            return

        files_to_process: List[str] = []
        skipped_initial = 0
        for fpath in all_files:
            base_no_ext, ext = os.path.splitext(fpath)
            if base_no_ext.endswith('C'):
                skipped_initial += 1
            else:
                files_to_process.append(fpath)
        
        total_actual_to_process = len(files_to_process)
        
        self.root.after_idle(lambda: progress_window.update_progress(
            processed=0,
            total=total_actual_to_process,
            skipped=skipped_initial
        ))

        if total_actual_to_process == 0:
            self._update_status_async("No new images to process in selected folder.")
            self.root.after_idle(lambda: progress_window.complete(0, 0, 0))
            self._show_messagebox_async('info', 'Batch Complete', 'No new images to process.')
            return

        self._update_status_async(f"Batch start: {total_actual_to_process} images to process", "#4CAF50")

        processed_count = 0
        failed_count = 0
        start_time = time.time()
        batch_threshold = 0.075  # fixed sensitivity per request
        
        first_file_end_time = None
        
        batch_cancelled = False

        for idx, fpath in enumerate(files_to_process, start=1):
            if stop_event.is_set():
                batch_cancelled = True
                break # Exit loop if stop event is set

            current_file_start_time = time.time()
            try:
                base_no_ext, ext = os.path.splitext(fpath)

                self._update_status_async(f"[{idx}/{total_actual_to_process}] Processing {os.path.basename(fpath)}...")
                self.root.after_idle(lambda: progress_window.status_label.configure(text=f"Processing {os.path.basename(fpath)}..."))

                # Load image
                with Image.open(fpath) as im:
                    img = im.convert('RGB')

                # Predict mask probabilities (tile-based)
                prob_mask = ImageProcessingService.predict_dust_mask(
                    self.state.unet_model,
                    img,
                    threshold=0.5,
                    window_size=1024,
                    stride=512,
                    device=self.state.device,
                    progress_callback=None
                )

                # Threshold to binary at desired sensitivity
                bin_mask = ImageProcessingService.create_binary_mask(prob_mask, batch_threshold, img.size)

                # Dilate for coverage
                dilated = ImageProcessingService.dilate_mask(bin_mask)

                # Inpaint (fast CV2) and blend
                inpainted = self.perform_cv2_inpainting(img, dilated)
                final_img = ImageProcessingService.blend_images(img, inpainted, dilated)

                # Output path with 'C' suffix
                out_path = base_no_ext + 'C' + ext
                if ext.lower() in (".jpg", ".jpeg"):
                    final_img.save(out_path, 'JPEG', quality=95)
                else:
                    final_img.save(out_path)

                processed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Batch error on {fpath}: {e}")
            finally:
                current_file_end_time = time.time()
                if first_file_end_time is None:
                    first_file_end_time = current_file_end_time
                
                elapsed_since_start = current_file_end_time - start_time
                files_done = processed_count + failed_count
                
                eta_seconds = None
                if files_done > 0:
                    avg_time_per_file = elapsed_since_start / files_done
                    remaining_files = total_actual_to_process - files_done
                    eta_seconds = avg_time_per_file * remaining_files

                self.root.after_idle(lambda: progress_window.update_progress(
                    processed=processed_count,
                    total=total_actual_to_process,
                    skipped=skipped_initial,
                    eta_seconds=eta_seconds
                ))
        
        if batch_cancelled:
            self._update_status_async(f"Batch cancelled by user. {processed_count} images processed.", "orange")
            self._show_messagebox_async('info', 'Batch Cancelled', f"Batch processing was cancelled. {processed_count} images processed.")
            self.root.after_idle(lambda: progress_window.complete(processed_count, total_actual_to_process, failed_count))
        else:
            elapsed_total = time.time() - start_time
            self._update_status_async(
                f"Batch done: {processed_count}/{total_actual_to_process} succeeded, {failed_count} failed in {elapsed_total:.1f}s",
                "#4CAF50" if failed_count == 0 else "orange"
            )
            self._show_messagebox_async('info', 'Batch Complete', f"Processed {processed_count}/{total_actual_to_process} images. Failed: {failed_count}.")
            self.root.after_idle(lambda: progress_window.complete(processed_count, total_actual_to_process, failed_count))
    except Exception as e:
        print(f"Batch fatal error: {e}")
        self._update_status_async(f"Batch failed: {e}", "red")
        self.root.after_idle(lambda: progress_window.complete(processed_count, total_actual_to_process, failed_count))
    finally:
        self._finish_batch_ui(progress_window)
