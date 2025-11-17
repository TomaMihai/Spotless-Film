# Spotless batch processing helpers for SpotlessFilmModern
from tkinter import messagebox, filedialog
from typing import Optional, List
import threading
import os
import time
from PIL import Image
import numpy as np

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

def _finish_batch_ui(self):
    def _do():
        try:
            self.batch_btn.configure(text="?? Batch Process Folder", state="normal")
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
        self.batch_btn.configure(text="?? Processing...", state="disabled")
    except Exception:
        pass
    t = threading.Thread(target=self._batch_process_folder_worker, args=(folder,))
    t.daemon = True
    t.start()

def _batch_process_folder_worker(self, root_folder: str):
    try:
        # Ensure model is available
        if not self.state.unet_model:
            self._update_status_async("Model not loaded. Please wait for models to load.", "red")
            self._show_messagebox_async('error', 'Batch Error', 'U-Net model not loaded. Please wait for models to load.')
            return

        supported_ext = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")
        files: List[str] = []
        for dirpath, _dirnames, filenames in os.walk(root_folder):
            for fname in filenames:
                if fname.lower().endswith(supported_ext):
                    files.append(os.path.join(dirpath, fname))

        total = len(files)
        if total == 0:
            self._update_status_async("No images found in selected folder.")
            return

        self._update_status_async(f"Batch start: {total} images", "#4CAF50")

        processed = 0
        failed = 0
        start = time.time()
        batch_threshold = 0.075  # fixed sensitivity per request

        for idx, fpath in enumerate(files, start=1):
            try:
                base_no_ext, ext = os.path.splitext(fpath)
                # Skip already-processed outputs (ending with 'C')
                if base_no_ext.endswith('C'):
                    continue

                self._update_status_async(f"[{idx}/{total}] Processing {os.path.basename(fpath)}...")

                # Load image
                with Image.open(fpath) as im:
                    img = im.convert('RGB')

                # Predict mask probabilities (tile-based)
                prob_mask = self.ImageProcessingService.predict_dust_mask(
                    self.state.unet_model,
                    img,
                    threshold=0.5,
                    window_size=1024,
                    stride=512,
                    device=self.state.device,
                    progress_callback=None
                )

                # Threshold to binary at desired sensitivity
                bin_mask = self.ImageProcessingService.create_binary_mask(prob_mask, batch_threshold, img.size)

                # Dilate for coverage
                dilated = self.ImageProcessingService.dilate_mask(bin_mask)

                # Inpaint (fast CV2) and blend
                inpainted = self.perform_cv2_inpainting(img, dilated)
                final_img = self.ImageProcessingService.blend_images(img, inpainted, dilated)

                # Output path with 'C' suffix
                out_path = base_no_ext + 'C' + ext
                if ext.lower() in (".jpg", ".jpeg"):
                    final_img.save(out_path, 'JPEG', quality=95)
                else:
                    final_img.save(out_path)

                processed += 1
            except Exception as e:
                failed += 1
                print(f"Batch error on {fpath}: {e}")

        elapsed = time.time() - start
        self._update_status_async(
            f"Batch done: {processed}/{total} succeeded, {failed} failed in {elapsed:.1f}s",
            "#4CAF50" if failed == 0 else "orange"
        )
        self._show_messagebox_async('info', 'Batch Complete', f"Processed {processed}/{total} images. Failed: {failed}.")
    except Exception as e:
        print(f"Batch fatal error: {e}")
        self._update_status_async(f"Batch failed: {e}", "red")
    finally:
        self._finish_batch_ui()
