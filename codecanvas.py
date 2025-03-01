import os
import json
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, font
from tkinter import messagebox
from pygments import lexers, formatters, highlight
from pygments.lexers import get_lexer_by_name
import pyperclip
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
from pygments.formatters import HtmlFormatter, ImageFormatter
import subprocess

class CodeEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Editor with Export")
        self.root.geometry("900x500")  # Larger default window size
        
        # Set a nice theme
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        self.project_path = None
        self.cells = []
        
        # Create a main frame with padding
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar with improved styling
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Improved buttons with icons (you can add icons later)
        self.open_button = ttk.Button(self.toolbar, text="Open Project", command=self.open_project, width=15)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.new_button = ttk.Button(self.toolbar, text="New Project", command=self.create_project, width=15)
        self.new_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.add_cell_button = ttk.Button(self.toolbar, text="Add Cell", command=self.add_cell, width=15)
        self.add_cell_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.download_all_button = ttk.Button(self.toolbar, text="Download All", command=self.download_all, width=15)
        self.download_all_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_button = ttk.Button(self.toolbar, text="Save Project", command=self.save_project, width=15)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.open_folder_button = ttk.Button(self.toolbar, text="Open Folder", command=self.open_folder, width=15)
        self.open_folder_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Create a canvas with scrollbar for the cells
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame inside canvas for cells
        self.cell_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cell_frame, anchor="nw")
        
        # Configure canvas to resize with window
        self.cell_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Mouse wheel scrolling for the main window
        # We'll handle mouse wheel events differently based on where the cursor is
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Status bar for messages
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
        
        # Default language options
        self.available_languages = [
            "python", "matlab", "bash", "java", "javascript", "html", 
            "css", "c", "cpp", "csharp", "php", "ruby", "swift", 
            "kotlin", "go", "rust", "r", "sql",  "powershell"
        ]
        
        # Track which widget has focus for scrolling behavior
        self.focused_text = None

    def on_frame_configure(self, event):
        # Update the scrollregion to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        # Update the width of the window to fit the canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        # Check if a text widget has focus
        focused = self.root.focus_get()
        
        # If the focused widget is a Text widget, let it handle scrolling
        if isinstance(focused, tk.Text) or isinstance(focused, scrolledtext.ScrolledText):
            # Let the widget handle its own scrolling
            # This event will propagate to the text widget's own bindings
            pass
        else:
            # If no text widget has focus, scroll the main canvas
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_project(self):
        project_dir = filedialog.askdirectory(title="Select Directory for New Project")
        if project_dir:
            self.project_path = project_dir
            file_path = os.path.join(self.project_path, "file.imgnb")
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    json.dump({"cells": []}, f)
            
            # Clear existing cells
            for cell in self.cells:
                cell.frame.destroy()
            self.cells.clear()
            
            self.status_var.set(f"Created new project in {project_dir}")
            self.root.title(f"Code Editor - {os.path.basename(project_dir)}")
            self.add_cell()  # Add an initial empty cell

    def open_project(self):
        project_dir = filedialog.askdirectory(title="Select Project Directory")
        if project_dir:
            self.project_path = project_dir
            file_path = os.path.join(self.project_path, "file.imgnb")
            
            # Clear existing cells
            for cell in self.cells:
                cell.frame.destroy()
            self.cells.clear()
            
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    try:
                        data = json.load(f)
                        for cell_data in data.get("cells", []):
                            self.add_cell(
                                cell_data.get("title", ""), 
                                cell_data.get("language", "python"), 
                                cell_data.get("code", "")
                            )
                        if not data.get("cells"):
                            self.add_cell()  # Add an empty cell if no cells exist
                    except json.JSONDecodeError:
                        messagebox.showwarning("Warning", "Project file is corrupted, creating a new one.")
                        with open(file_path, "w") as f:
                            json.dump({"cells": []}, f)
                        self.add_cell()  # Add an empty cell
            else:
                with open(file_path, "w") as f:
                    json.dump({"cells": []}, f)
                self.add_cell()  # Add an empty cell
            
            self.status_var.set(f"Opened project from {project_dir}")
            self.root.title(f"Code Editor - {os.path.basename(project_dir)}")

    def add_cell(self, title="", language="python", code=""):
        cell = CodeCell(self.cell_frame, self, title, language, code)
        self.cells.append(cell)
        cell.frame.pack(fill=tk.X, padx=5, pady=5, expand=True)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Scroll to the new cell
        self.canvas.yview_moveto(1.0)

    def download_all(self):
        if not self.project_path:
            self.status_var.set("No project opened. Please open or create a project first.")
            return
        
        images_folder = os.path.join(self.project_path, "images")
        os.makedirs(images_folder, exist_ok=True)
        
        success_count = 0
        for cell in self.cells:
            if cell.download_image(images_folder):
                success_count += 1
        
        self.save_project()
        self.status_var.set(f"Downloaded {success_count} images to {images_folder}")

    def save_project(self):
        if not self.project_path:
            self.status_var.set("No project opened. Please open or create a project first.")
            return
        
        file_path = os.path.join(self.project_path, "file.imgnb")
        data = {"cells": []}
        
        for cell in self.cells:
            data["cells"].append({
                "title": cell.title_entry.get(),
                "language": cell.language.get(),
                "code": cell.text.get("1.0", tk.END).strip()
            })
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        
        self.status_var.set("Project saved successfully!")

    def open_folder(self, folder=None):
        if not self.project_path:
            self.status_var.set("No project opened. Please open or create a project first.")
            return

        if folder is None and self.project_path:
            folder = os.path.join(self.project_path, "images")
            os.makedirs(folder, exist_ok=True)
            if os.name == 'posix':
                subprocess.Popen(['xdg-open', folder])
            else:
                os.startfile(folder)
            # subprocess.Popen(folder)
        elif folder is not None:
            if os.name == 'posix':
                subprocess.Popen(['xdg-open', folder])
            else:
                os.startfile(folder)
            # os.startfile(folder)
            # subprocess.Popen()

class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind('<KeyRelease>', self.redraw)
        self.text_widget.bind('<Configure>', self.redraw)
        self.text_widget.bind('<<Change>>', self.redraw)
        self.text_widget.bind('<MouseWheel>', self.redraw)
        self.text_widget.bind('<Button-1>', self.redraw)  # Redraw on click
        self.text_widget.bind('<FocusIn>', self.redraw)   # Redraw when getting focus
        
        self.font = font.Font(family="Consolas", size=11)
        
    def redraw(self, *args):
        """Redraw line numbers"""
        self.delete("all")
        
        # Get the first and last visible line
        first_index = self.text_widget.index("@0,0")
        last_index = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
        
        first_line = int(first_index.split('.')[0])
        last_line = int(last_index.split('.')[0])
        
        # Draw line numbers
        y_pos = 2  # Starting y position
        for line_num in range(first_line, last_line + 1):
            line_text = str(line_num)
            x_pos = self.winfo_width() - 5  # Right-aligned
            
            # Get y coordinate of line
            index = f"{line_num}.0"
            bbox = self.text_widget.bbox(index)
            if bbox is not None:
                y_pos = bbox[1]  # Use actual y position
                self.create_text(x_pos, y_pos, anchor='ne', text=line_text, 
                                font=self.font, fill="#606060")

class CodeCell:
    def __init__(self, parent, app, title="", language="python", code=""):
        self.app = app
        
        # Create a frame with better appearance
        self.frame = ttk.Frame(parent, style="Card.TFrame")
        self.frame.configure(padding=10)
        
        # Add a header frame for title and controls
        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Title label and entry
        ttk.Label(self.header_frame, text="Title:").pack(side=tk.LEFT, padx=(0, 5))
        self.title_entry = ttk.Entry(self.header_frame, width=40)
        self.title_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.title_entry.insert(0, title)
        
        # Language selection
        ttk.Label(self.header_frame, text="Language:").pack(side=tk.LEFT, padx=(0, 5))
        self.language = tk.StringVar()
        self.language_dropdown = ttk.Combobox(
            self.header_frame, 
            textvariable=self.language, 
            values=app.available_languages, 
            state="readonly",
            width=15
        )
        self.language_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        self.language_dropdown.set(language)
        
        # Code editor frame
        self.editor_frame = ttk.Frame(self.frame, borderwidth=1, relief="sunken")
        self.editor_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a custom font for the code
        custom_font = font.Font(family="Consolas", size=11)
        
        # Create text widget for code (NOT using ScrolledText - we'll add scrollbars manually)
        self.text = tk.Text(
            self.editor_frame, 
            height=15,
            width=80,
            wrap=tk.NONE,
            font=custom_font,
            background="#f8f8f8",
            foreground="#333333",
            insertbackground="#333333",
            undo=True,
            padx=5,
            pady=5
        )
        
        # Create line numbers
        self.line_numbers = LineNumbers(
            self.editor_frame, 
            self.text, 
            width=30,
            background="#f0f0f0", 
            bd=0, 
            highlightthickness=0
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Add scrollbars
        self.y_scrollbar = ttk.Scrollbar(self.editor_frame, orient="vertical", command=self.text.yview)
        self.x_scrollbar = ttk.Scrollbar(self.editor_frame, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=self.y_scrollbar.set, xscrollcommand=self.x_scrollbar.set)
        
        # Pack everything
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Insert initial code
        self.text.insert("1.0", code)
        
        # Add tab support
        self.text.bind("<Tab>", self.handle_tab)
        
        # Handle mousewheel for text widget scrolling
        self.text.bind("<MouseWheel>", self.on_mousewheel)
        
        # Force redraw of line numbers when text widget scrolls
        self.text.bind("<<ScrolledText>>", lambda e: self.line_numbers.redraw())
        
        # Bottom toolbar for actions
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons with better styling
        self.download_button = ttk.Button(
            self.button_frame, 
            text="Download as Image", 
            command=self.download_image,
            width=20
        )
        self.download_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.copy_button = ttk.Button(
            self.button_frame, 
            text="Copy to Clipboard", 
            command=self.copy_to_clipboard,
            width=20
        )
        self.copy_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.remove_button = ttk.Button(
            self.button_frame, 
            text="Remove Cell", 
            command=self.remove_cell,
            width=15
        )
        self.remove_button.pack(side=tk.RIGHT)
        
        # Force initial line numbers update
        self.line_numbers.redraw()

    def on_mousewheel(self, event):
        # Scroll the text widget (not the main canvas)
        self.text.yview_scroll(int(-1*(event.delta/120)), "units")
        # Update line numbers when scrolling
        self.line_numbers.redraw()
        # Stop propagation to prevent the main canvas from scrolling
        return "break"

    def handle_tab(self, event):
        # Insert spaces instead of a tab character
        self.text.insert(tk.INSERT, "    ")
        return "break"  # Prevent default tab behavior

    def download_image(self, folder=None, include_circles=False):
        title = self.title_entry.get().strip() or "untitled"
        code = self.text.get("1.0", tk.END).strip()
        lang = self.language.get()
        
        if not code:
            self.app.status_var.set("Cannot export empty code cell")
            return False
        
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
            
            # Create custom formatter with Carbon.sh-inspired styling
            formatter = ImageFormatter(
                font_name="Consolas",
                font_size=14,
                line_numbers=True,
                line_number_bg="#DFE0E1", #"#222831",  # Darker background for line numbers
                line_number_fg="#606F85",  # Subtle color for line numbers
                line_number_bold=False,    # More subtle line numbers
                style="default", # "github-dark",    # Modern dark theme
                image_padding=30,          # More generous padding
                image_bg="#DFE0E1",        # Dark background (matches Carbon default)
                line_pad=6,                # Better line spacing
                line_number_separator=False # Remove the separator line
            )
            
            highlighted_code = highlight(code, lexer, formatter)
            
            # Determine the folder to save in
            if folder is None and self.app.project_path:
                folder = os.path.join(self.app.project_path, "images")
                os.makedirs(folder, exist_ok=True)
            
            if folder:
                # Create a clean filename
                clean_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
                image_path = os.path.join(folder, f"{clean_title}.png")
                
                # Open the base image
                img = Image.open(io.BytesIO(highlighted_code))
                width, height = img.size
                
                # Create a new image with rounded corners and padding
                # Add extra space for title and add gradient background
                title_height = 25
                title_size = 15
                new_height = height + title_height if title else height
                new_img = Image.new('RGBA', (width, new_height), (0, 0, 0, 0))
                
                # Create a gradient background
                background = Image.new('RGBA', (width, new_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(background)
                
                # Create gradient from top to bottom
                for y in range(new_height):
                    # Gradient from #1F2430 to slightly lighter #262D3D
                    r = int(31 + (y / new_height) * 7)
                    g = int(36 + (y / new_height) * 9)
                    b = int(48 + (y / new_height) * 13)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
                
                # Add rounded corners to the background
                radius = 12
                circle = Image.new('L', (radius * 2, radius * 2), 0)
                draw = ImageDraw.Draw(circle)
                draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
                
                # Apply rounded corners to the background
                alpha = Image.new('L', background.size, 255)
                # Top left
                alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
                # Top right
                alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (width - radius, 0))
                # Bottom left
                alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, new_height - radius))
                # Bottom right
                alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (width - radius, new_height - radius))
                
                # Apply the alpha mask to the background
                background.putalpha(alpha)
                
                # Paste the original image onto the new background
                y_offset = title_height if title else 0
                new_img.paste(background, (0, 0))
                new_img.paste(img, (0, y_offset), img if img.mode == 'RGBA' else None)
                
                # Add a window control UI element for that modern app look
                if title:
                    draw = ImageDraw.Draw(new_img)
                    # Draw title text
                    try:
                        title_font = ImageFont.truetype("arial.ttf", title_size)
                    except IOError:
                        print("Font not found")
                        title_font = ImageFont.load_default()
                    
                    # # Add window controls (circles) for the macOS look
                    if include_circles:                   
                        circle_y = 25
                        # Red circle
                        draw.ellipse((15, circle_y - 6, 15 + 12, circle_y + 6), fill="#FF5F56")
                        # Yellow circle
                        draw.ellipse((35, circle_y - 6, 35 + 12, circle_y + 6), fill="#FFBD2E")
                        # Green circle
                        draw.ellipse((55, circle_y - 6, 55 + 12, circle_y + 6), fill="#27C93F")
                    
                    # Draw title text (centered)
                    text_width = title_font.getlength(title) if hasattr(title_font, 'getlength') else draw.textlength(title, font=title_font)
                    text_x = (width - text_width) // 2
                    draw.text((text_x, 5), title, font=title_font, fill="#FFFFFF")
                
                # Add drop shadow effect
                shadow = Image.new('RGBA', (width + 20, new_height + 20), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_rect = [(10, 10), (width + 10, new_height + 10)]
                shadow_draw.rectangle(shadow_rect, fill=(0, 0, 0, 20))
                shadow = shadow.filter(ImageFilter.GaussianBlur(10))
                
                # Create the final image with shadow
                final_image = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
                final_image.paste(shadow, (0, 0))
                final_image.paste(new_img, (10, 10), new_img)
                
                # Save with transparency
                final_image.save(image_path)
                
                self.app.status_var.set(f"Saved: {image_path}")
                return True
            else:
                self.app.status_var.set("No project opened. Please open or create a project first.")
                return False
                
        except Exception as e:
            self.app.status_var.set(f"Error exporting image: {str(e)}")
            import traceback
            traceback.print_exc()  # Print detailed error for debugging
            return False
    
    def copy_to_clipboard(self):
        code = self.text.get("1.0", tk.END).strip()
        if code:
            pyperclip.copy(code)
            self.app.status_var.set("Code copied to clipboard")
        else:
            self.app.status_var.set("Nothing to copy - code cell is empty")

    def remove_cell(self):
        if len(self.app.cells) > 1:
            self.app.cells.remove(self)
            self.frame.destroy()
            self.app.canvas.configure(scrollregion=self.app.canvas.bbox("all"))
            self.app.status_var.set("Cell removed")
        else:
            self.app.status_var.set("Cannot remove the last cell")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditorApp(root)
    root.mainloop()