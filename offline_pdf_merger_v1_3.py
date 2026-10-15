import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import DANGER, PRIMARY, SECONDARY, SUCCESS
    MODERN_THEME = True
except ImportError:
    tb = None
    MODERN_THEME = False
    PRIMARY = SECONDARY = SUCCESS = DANGER = None

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter

try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
    PYMUPDF_IMPORT_ERROR = ""
except Exception as error:
    pymupdf = None
    PYMUPDF_AVAILABLE = False
    PYMUPDF_IMPORT_ERROR = str(error)

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    PIL_IMPORT_ERROR = ""
except Exception as error:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False
    PIL_IMPORT_ERROR = str(error)

THUMBNAILS_AVAILABLE = PYMUPDF_AVAILABLE and PIL_AVAILABLE


def resource_path(relative_path):
    """Return the correct path in source mode and PyInstaller one-file mode."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline PDF Merger by Uren")
        self.root.geometry("1200x820")
        self.root.minsize(850, 560)

        self.pdf_files = []
        self.thumbnail_cache = {}
        self.card_widgets = []
        self.selected_indices = set()
        self.last_selected_index = None
        self.view_mode = "grid"
        self.maximum_grid_columns = 5
        self.minimum_card_width = 225
        self.resize_job = None

        self.app_name = "Offline PDF Merger"
        self.app_version = "1.3"
        self.developer_name = "Uren Thummar"
        self.developer_email = "33000kv@gmail.com"
        self.developer_phone = "+91 88663 03946"

        self.set_window_icon(self.root)
        self.build_ui()

    def set_window_icon(self, window):
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            try:
                window.iconbitmap(icon_path)
            except Exception:
                pass

    def make_button(self, parent, text, command, style=None):
        if MODERN_THEME:
            return tb.Button(parent, text=text, command=command, bootstyle=style or SECONDARY)
        return ttk.Button(parent, text=text, command=command)

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text=self.app_name, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Select, preview, rearrange and merge PDF files. Nothing is uploaded.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 14))

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(0, 10))
        self.make_button(toolbar, "+ Add PDFs", self.add_files, PRIMARY).pack(side="left", padx=(0, 7))
        self.make_button(toolbar, "Move up", lambda: self.move_selected(-1)).pack(side="left", padx=4)
        self.make_button(toolbar, "Move down", lambda: self.move_selected(1)).pack(side="left", padx=4)
        self.make_button(toolbar, "Remove selected", self.remove_selected, DANGER).pack(side="left", padx=4)
        self.make_button(toolbar, "Clear", self.clear_all).pack(side="left", padx=4)

        self.view_button = self.make_button(toolbar, "List view", self.toggle_view, SECONDARY)
        self.view_button.pack(side="left", padx=(12, 4))

        main = ttk.Frame(outer)
        main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main, highlightthickness=0, bg="#f3f5f7")
        self.scrollbar = ttk.Scrollbar(main, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg="#f3f5f7")
        self.list_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.list_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(12, 0))
        self.status = ttk.Label(footer, text="No files selected")
        self.status.pack(side="left")
        self.make_button(footer, "About", self.show_about, SECONDARY).pack(side="right", padx=(0, 8))
        self.make_button(footer, "Create merged PDF", self.merge, SUCCESS).pack(side="right")

        self.render_cards()

    def update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event):
        self.canvas.itemconfigure(self.list_window, width=event.width)
        if self.view_mode == "grid" and self.pdf_files:
            if self.resize_job is not None:
                self.root.after_cancel(self.resize_job)
            self.resize_job = self.root.after(150, self.render_cards)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")],
        )
        for path in paths:
            normalized = os.path.normpath(path)
            if normalized not in self.pdf_files:
                self.pdf_files.append(normalized)
        self.selected_indices.clear()
        self.last_selected_index = None
        self.render_cards()

    def thumbnail(self, path, width, height):
        cache_key = (path, width, height)
        if cache_key in self.thumbnail_cache:
            return self.thumbnail_cache[cache_key]
        if not THUMBNAILS_AVAILABLE:
            return None

        document = None
        try:
            document = pymupdf.open(path)
            if document.page_count == 0:
                return None

            page = document.load_page(0)
            page_rect = page.rect
            scale = min(width / page_rect.width, height / page_rect.height)
            scale = max(scale, 0.35)
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(scale, scale),
                alpha=False,
                colorspace=pymupdf.csRGB,
            )
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.thumbnail_cache[cache_key] = photo
            return photo
        except Exception as error:
            print(f"Thumbnail failed for {Path(path).name}: {error}")
            return None
        finally:
            if document is not None:
                document.close()

    def preview_fallback_text(self):
        if not PYMUPDF_AVAILABLE:
            return "Preview unavailable\nPyMuPDF missing"
        if not PIL_AVAILABLE:
            return "Preview unavailable\nPillow missing"
        return "Preview unavailable"

    def toggle_view(self):
        self.view_mode = "list" if self.view_mode == "grid" else "grid"
        self.view_button.configure(text="Grid view" if self.view_mode == "list" else "List view")
        self.canvas.yview_moveto(0)
        self.render_cards()

    def clear_render_area(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        for column in range(self.maximum_grid_columns + 1):
            self.list_frame.grid_columnconfigure(column, weight=0, uniform="")
        self.card_widgets = []

    def render_cards(self):
        self.resize_job = None
        self.clear_render_area()

        if not self.pdf_files:
            empty_box = tk.Frame(self.list_frame, bg="#f3f5f7", padx=60, pady=60)
            empty_box.grid(row=0, column=0, sticky="nsew")
            self.list_frame.grid_columnconfigure(0, weight=1)
            tk.Label(
                empty_box,
                text="No PDF files added",
                bg="#f3f5f7",
                font=("Segoe UI", 14, "bold"),
            ).pack()
            tk.Label(
                empty_box,
                text="Use Add PDFs to select multiple files.",
                bg="#f3f5f7",
            ).pack(pady=6)
            self.status.configure(text="No files selected")
            self.update_scroll_region()
            return

        if self.view_mode == "grid":
            self.render_grid_cards()
        else:
            self.render_list_cards()

        total_mb = sum(
            os.path.getsize(path) for path in self.pdf_files if os.path.exists(path)
        ) / (1024 * 1024)
        self.status.configure(
            text=(
                f"{len(self.pdf_files)} file(s) | {len(self.selected_indices)} selected | "
                f"{total_mb:.2f} MB | Shift selects a range, Ctrl selects individual files"
            )
        )
        self.root.after_idle(self.update_scroll_region)

    def render_grid_cards(self):
        available_width = max(self.canvas.winfo_width(), 850)
        columns = max(1, min(self.maximum_grid_columns, available_width // self.minimum_card_width))

        for column in range(columns):
            self.list_frame.grid_columnconfigure(column, weight=1, uniform="pdf_cards")

        for index, path in enumerate(self.pdf_files):
            row, column = divmod(index, columns)
            selected = index in self.selected_indices
            bg = "#dce8ff" if selected else "#ffffff"
            border = "#292662" if selected else "#c5cbd3"

            card = tk.Frame(
                self.list_frame,
                bg=bg,
                highlightthickness=2 if selected else 1,
                highlightbackground=border,
                cursor="hand2",
            )
            card.grid(row=row, column=column, sticky="nsew", padx=7, pady=7)
            card.grid_columnconfigure(0, weight=1)

            header = tk.Frame(card, bg=bg)
            header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
            order = tk.Label(
                header,
                text=f"{index + 1:02d}",
                bg="#292662",
                fg="#ffffff",
                font=("Segoe UI", 9, "bold"),
                padx=7,
                pady=3,
            )
            order.pack(side="left")
            remove = tk.Button(
                header,
                text="Remove",
                command=lambda x=index: self.remove_one(x),
                relief="flat",
                bd=0,
                bg=bg,
                activebackground=bg,
                fg="#b42318",
                activeforeground="#b42318",
                cursor="hand2",
                font=("Segoe UI", 8),
            )
            remove.pack(side="right")

            thumb = self.thumbnail(path, 130, 170)
            if thumb:
                preview = tk.Label(card, image=thumb, bg=bg, width=140, height=180)
            else:
                preview = tk.Label(
                    card,
                    text=self.preview_fallback_text(),
                    bg="#e9edf2",
                    fg="#52606d",
                    width=18,
                    height=10,
                    font=("Segoe UI", 8),
                    justify="center",
                )
            preview.grid(row=1, column=0, pady=(8, 7))

            name = tk.Label(
                card,
                text=Path(path).name,
                bg=bg,
                fg="#111827",
                font=("Segoe UI", 9, "bold"),
                justify="center",
                wraplength=190,
            )
            name.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))

            details = tk.Label(
                card,
                text=self.file_details(path),
                bg=bg,
                fg="#52606d",
                font=("Segoe UI", 8),
            )
            details.grid(row=3, column=0, pady=(0, 11))

            for widget in (card, header, order, preview, name, details):
                widget.bind("<Button-1>", lambda event, x=index: self.select_card(event, x))
            self.card_widgets.append(card)

    def render_list_cards(self):
        self.list_frame.grid_columnconfigure(0, weight=1)
        for index, path in enumerate(self.pdf_files):
            selected = index in self.selected_indices
            bg = "#dce8ff" if selected else "#ffffff"
            border = "#292662" if selected else "#c5cbd3"

            card = tk.Frame(
                self.list_frame,
                bg=bg,
                highlightthickness=2 if selected else 1,
                highlightbackground=border,
            )
            card.grid(row=index, column=0, sticky="ew", padx=8, pady=5)
            card.grid_columnconfigure(2, weight=1)

            order = tk.Label(card, text=str(index + 1), width=3, bg=bg, font=("Segoe UI", 11, "bold"))
            order.grid(row=0, column=0, rowspan=2, padx=(10, 3), pady=10)

            thumb = self.thumbnail(path, 75, 95)
            if thumb:
                preview = tk.Label(card, image=thumb, bg=bg, width=82, height=102)
            else:
                preview = tk.Label(
                    card,
                    text=self.preview_fallback_text(),
                    bg="#e9edf2",
                    fg="#52606d",
                    width=17,
                    height=7,
                    font=("Segoe UI", 8),
                    justify="center",
                )
            preview.grid(row=0, column=1, rowspan=2, padx=8, pady=8)

            name = tk.Label(
                card,
                text=Path(path).name,
                anchor="w",
                bg=bg,
                font=("Segoe UI", 11, "bold"),
            )
            name.grid(row=0, column=2, sticky="ew", padx=8, pady=(16, 2))

            details = tk.Label(
                card,
                text=self.file_details(path),
                anchor="w",
                bg=bg,
                fg="#52606d",
                font=("Segoe UI", 9),
            )
            details.grid(row=1, column=2, sticky="new", padx=8, pady=(2, 14))

            remove = tk.Button(
                card,
                text="Remove",
                command=lambda x=index: self.remove_one(x),
                relief="flat",
                bd=0,
                bg=bg,
                activebackground=bg,
                fg="#b42318",
                activeforeground="#b42318",
                cursor="hand2",
            )
            remove.grid(row=0, column=3, rowspan=2, padx=12)

            for widget in (card, order, preview, name, details):
                widget.bind("<Button-1>", lambda event, x=index: self.select_card(event, x))
            self.card_widgets.append(card)

    def file_details(self, path):
        try:
            pages = len(PdfReader(path).pages)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            return f"{pages} page(s) | {size_mb:.2f} MB"
        except Exception:
            return "Unable to read file"

    def select_card(self, event, index):
        ctrl = bool(event.state & 0x0004)
        shift = bool(event.state & 0x0001)

        if shift and self.last_selected_index is not None:
            start, end = sorted((self.last_selected_index, index))
            if not ctrl:
                self.selected_indices.clear()
            self.selected_indices.update(range(start, end + 1))
        elif ctrl:
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.add(index)
            self.last_selected_index = index
        else:
            self.selected_indices = {index}
            self.last_selected_index = index
        self.render_cards()

    def move_selected(self, direction):
        if not self.selected_indices:
            messagebox.showinfo("Select files", "Select one or more files first.")
            return

        selected = sorted(self.selected_indices)
        if direction < 0:
            if selected[0] == 0:
                return
            for index in selected:
                self.pdf_files[index - 1], self.pdf_files[index] = self.pdf_files[index], self.pdf_files[index - 1]
            self.selected_indices = {index - 1 for index in selected}
            self.last_selected_index = min(self.selected_indices)
        else:
            if selected[-1] == len(self.pdf_files) - 1:
                return
            for index in reversed(selected):
                self.pdf_files[index + 1], self.pdf_files[index] = self.pdf_files[index], self.pdf_files[index + 1]
            self.selected_indices = {index + 1 for index in selected}
            self.last_selected_index = max(self.selected_indices)
        self.render_cards()

    def remove_one(self, index):
        removed_path = self.pdf_files.pop(index)
        for key in list(self.thumbnail_cache):
            if key[0] == removed_path:
                self.thumbnail_cache.pop(key, None)
        self.selected_indices.clear()
        self.last_selected_index = None
        self.render_cards()

    def remove_selected(self):
        if not self.selected_indices:
            return
        removed_paths = [self.pdf_files[index] for index in self.selected_indices]
        for index in sorted(self.selected_indices, reverse=True):
            self.pdf_files.pop(index)
        for key in list(self.thumbnail_cache):
            if key[0] in removed_paths:
                self.thumbnail_cache.pop(key, None)
        self.selected_indices.clear()
        self.last_selected_index = None
        self.render_cards()

    def clear_all(self):
        if self.pdf_files and messagebox.askyesno("Clear list", "Remove all files from the list?"):
            self.pdf_files.clear()
            self.selected_indices.clear()
            self.last_selected_index = None
            self.thumbnail_cache.clear()
            self.render_cards()

    def show_about(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"About {self.app_name}")
        dialog_width, dialog_height = 620, 510
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.set_window_icon(dialog)

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{max(x, 0)}+{max(y, 0)}")

        shell = tk.Frame(dialog, bg="#ffffff")
        shell.pack(fill="both", expand=True)
        hero = tk.Frame(shell, bg="#292662", height=135)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        tk.Label(
            hero,
            text="PDF",
            bg="#70B865",
            fg="#ffffff",
            font=("Segoe UI", 16, "bold"),
            width=5,
            height=2,
        ).pack(side="left", padx=(30, 20), pady=30)

        hero_text = tk.Frame(hero, bg="#292662")
        hero_text.pack(side="left", fill="both", expand=True, pady=(23, 18))
        tk.Label(
            hero_text,
            text=self.app_name,
            bg="#292662",
            fg="#ffffff",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            hero_text,
            text=f"Version {self.app_version} | Offline desktop utility",
            bg="#292662",
            fg="#E1E8F6",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(6, 0))

        body = tk.Frame(shell, bg="#ffffff", padx=32, pady=22)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text=(
                "A private, offline tool for arranging and merging PDF files. "
                "Documents remain on your computer and are not uploaded."
            ),
            bg="#ffffff",
            fg="#263238",
            font=("Segoe UI", 10),
            justify="left",
            wraplength=545,
        ).pack(anchor="w")
        tk.Frame(body, bg="#e5e7eb", height=1).pack(fill="x", pady=17)
        tk.Label(
            body,
            text=f"Made by {self.developer_name} with AI assistance",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        contact = tk.Frame(body, bg="#f6f7fb", padx=16, pady=13)
        contact.pack(fill="x", pady=(12, 0))
        tk.Label(contact, text="CONTACT", bg="#f6f7fb", fg="#292662", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(contact, text=f"Email: {self.developer_email}", bg="#f6f7fb", fg="#374151", font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(5, 2))
        tk.Label(contact, text=f"Phone: {self.developer_phone}", bg="#f6f7fb", fg="#374151", font=("Segoe UI", 9), anchor="w").pack(fill="x")

        actions = tk.Frame(body, bg="#ffffff")
        actions.pack(fill="x", pady=(18, 0))
        close_button = self.make_button(actions, "Close", dialog.destroy, PRIMARY)
        close_button.pack(side="right")
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        close_button.focus_set()
        self.root.wait_window(dialog)

    def merge(self):
        if not self.pdf_files:
            messagebox.showwarning("No files", "Add at least one PDF file.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile="Merged_Document.pdf",
            filetypes=[("PDF file", "*.pdf")],
        )
        if not output_path:
            return

        writer = PdfWriter()
        page_count = 0
        try:
            for path in self.pdf_files:
                reader = PdfReader(path)
                if reader.is_encrypted and not reader.decrypt(""):
                    raise ValueError(f"Password-protected file: {Path(path).name}")
                for page in reader.pages:
                    writer.add_page(page)
                    page_count += 1
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            messagebox.showinfo(
                "Completed",
                f"Merged PDF created successfully.\n\n{page_count} pages\n{output_path}",
            )
        except Exception as error:
            messagebox.showerror("Merge failed", str(error))


def main():
    if MODERN_THEME:
        root = tb.Window(themename="litera")
    else:
        root = tk.Tk()
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    PDFMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
