import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import difflib
from pathlib import Path
from datetime import datetime
import json
from functools import lru_cache
import threading
from typing import List, Tuple, Optional
import os
import mmap
import io

class TextFileComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("Text File Comparator")
        self.root.geometry("1000x800")
        
        # File paths and content cache
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self._file1_content: Optional[List[str]] = None
        self._file2_content: Optional[List[str]] = None
        
        # Store diff results
        self.diff_results = None
        
        # Store JSON validation results
        self.json_valid1 = False
        self.json_valid2 = False
        
        # Threading lock
        self.lock = threading.Lock()
        
        # Create a progress bar
        self.progress_var = tk.DoubleVar()
        
        self.create_widgets()
        
        # Bind file path changes to content cache clearing
        self.file1_path.trace('w', lambda *args: self.clear_cache(1))
        self.file2_path.trace('w', lambda *args: self.clear_cache(2))
    
    def create_widgets(self):
        # Main container with grid layout
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_container, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        file_frame.grid_columnconfigure(1, weight=1)
        
        # File 1 selection
        ttk.Label(file_frame, text="File 1:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.file1_path, width=50).grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(1)).grid(row=0, column=2, padx=5, pady=5)
        self.json_status1 = ttk.Label(file_frame, text="")
        self.json_status1.grid(row=0, column=3, padx=5, pady=5)
        
        # File 2 selection
        ttk.Label(file_frame, text="File 2:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.file2_path, width=50).grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(2)).grid(row=1, column=2, padx=5, pady=5)
        self.json_status2 = ttk.Label(file_frame, text="")
        self.json_status2.grid(row=1, column=3, padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_container)
        button_frame.grid(row=1, column=0, pady=5, sticky='ew')
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Buttons with improved layout
        self.compare_button = ttk.Button(button_frame, text="Compare Files", command=self.compare_files_threaded)
        self.compare_button.pack(side=tk.LEFT, padx=5)
        
        self.report_button = ttk.Button(button_frame, text="Generate Report", command=self.generate_report_threaded, state=tk.DISABLED)
        self.report_button.pack(side=tk.LEFT, padx=5)
        
        self.validate_json_button = ttk.Button(button_frame, text="Validate JSON", command=self.validate_json, state=tk.DISABLED)
        self.validate_json_button.pack(side=tk.LEFT, padx=5)
        
        self.format_json_button = ttk.Button(button_frame, text="Format JSON", command=self.format_json_threaded, state=tk.DISABLED)
        self.format_json_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_container, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, sticky='ew', pady=5)
        
        # Results frame with improved layout
        results_frame = ttk.LabelFrame(main_container, text="Comparison Results", padding="5")
        results_frame.grid(row=3, column=0, sticky='nsew', pady=5)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_columnconfigure(1, weight=1)
        
        # Configure main container row weights
        main_container.grid_rowconfigure(3, weight=1)
        
        # Text areas for comparison with improved configuration
        self.text_area1 = scrolledtext.ScrolledText(results_frame, wrap=tk.NONE, width=50, height=30)
        self.text_area1.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        self.text_area2 = scrolledtext.ScrolledText(results_frame, wrap=tk.NONE, width=50, height=30)
        self.text_area2.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        
        # Horizontal scrollbars
        h_scroll1 = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.text_area1.xview)
        h_scroll1.grid(row=1, column=0, sticky='ew')
        self.text_area1.configure(xscrollcommand=h_scroll1.set)
        
        h_scroll2 = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.text_area2.xview)
        h_scroll2.grid(row=1, column=1, sticky='ew')
        self.text_area2.configure(xscrollcommand=h_scroll2.set)
        
        # Bind scroll events for synchronization
        self.text_area1.bind('<MouseWheel>', lambda e: self.sync_scroll_mousewheel(e, self.text_area2))
        self.text_area2.bind('<MouseWheel>', lambda e: self.sync_scroll_mousewheel(e, self.text_area1))
        
        # Bind keyboard scrolling
        self.text_area1.bind('<Key-Up>', lambda e: self.sync_scroll_key(e, self.text_area2))
        self.text_area1.bind('<Key-Down>', lambda e: self.sync_scroll_key(e, self.text_area2))
        self.text_area2.bind('<Key-Up>', lambda e: self.sync_scroll_key(e, self.text_area1))
        self.text_area2.bind('<Key-Down>', lambda e: self.sync_scroll_key(e, self.text_area1))
    
    def browse_file(self, file_num):
        filename = filedialog.askopenfilename(
            title=f"Select File {file_num}",
            filetypes=[("Text/JSON Files", "*.txt *.json"), ("All Files", "*.*")]
        )
        if filename:
            if file_num == 1:
                self.file1_path.set(filename)
                self.check_json_validity(1)
            else:
                self.file2_path.set(filename)
                self.check_json_validity(2)
            
            # Enable validate and format buttons if both files are selected
            if self.file1_path.get() and self.file2_path.get():
                self.validate_json_button.config(state=tk.NORMAL)
                self.format_json_button.config(state=tk.NORMAL)
    
    def validate_json(self):
        """Validate both files for JSON format"""
        self.check_json_validity(1)
        self.check_json_validity(2)
        
        if self.json_valid1 and self.json_valid2:
            messagebox.showinfo("JSON Validation", "Both files contain valid JSON!")
        else:
            invalid_files = []
            if not self.json_valid1:
                invalid_files.append("File 1")
            if not self.json_valid2:
                invalid_files.append("File 2")
            messagebox.showerror("JSON Validation", 
                               f"Invalid JSON in: {', '.join(invalid_files)}\n"
                               "Please check the file contents and format.")
    
    def check_json_validity(self, file_num):
        """Check if a file contains valid JSON"""
        try:
            file_path = self.file1_path.get() if file_num == 1 else self.file2_path.get()
            status_label = self.json_status1 if file_num == 1 else self.json_status2
            
            if not file_path:
                status_label.config(text="")
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # Empty file
                    status_label.config(text="Empty file", foreground="orange")
                    return
                    
                json.loads(content)  # Try to parse JSON
                status_label.config(text="Valid JSON ✓", foreground="green")
                if file_num == 1:
                    self.json_valid1 = True
                else:
                    self.json_valid2 = True
                    
        except json.JSONDecodeError:
            status_label.config(text="Invalid JSON ✗", foreground="red")
            if file_num == 1:
                self.json_valid1 = False
            else:
                self.json_valid2 = False
        except Exception as e:
            status_label.config(text="Error reading file", foreground="red")
            if file_num == 1:
                self.json_valid1 = False
            else:
                self.json_valid2 = False
    
    def sync_scroll_mousewheel(self, event, target):
        """Synchronize scrolling between text areas for mousewheel events"""
        target.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    
    def sync_scroll_key(self, event, target):
        """Synchronize scrolling between text areas for keyboard events"""
        if event.keysym == 'Up':
            target.yview_scroll(-1, "units")
        elif event.keysym == 'Down':
            target.yview_scroll(1, "units")
        return "break"
    
    def clear_cache(self, file_num: int):
        """Clear the cached content when file paths change"""
        if file_num == 1:
            self._file1_content = None
        else:
            self._file2_content = None
    
    @lru_cache(maxsize=128)
    def read_file_efficient(self, file_path: str) -> List[str]:
        """Efficiently read file content using memory mapping for large files"""
        file_size = os.path.getsize(file_path)
        
        if file_size > 10 * 1024 * 1024:  # 10MB threshold for memory mapping
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode('utf-8')
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        return content.splitlines(keepends=True)
    
    def compare_files_threaded(self):
        """Start file comparison in a separate thread"""
        if not self.file1_path.get() or not self.file2_path.get():
            messagebox.showerror("Error", "Please select both files to compare")
            return
            
        self.compare_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self._compare_files_worker)
        thread.daemon = True
        thread.start()
    
    def _compare_files_worker(self):
        """Worker function for file comparison"""
        try:
            # Clear previous content
            self.root.after(0, lambda: self.text_area1.delete(1.0, tk.END))
            self.root.after(0, lambda: self.text_area2.delete(1.0, tk.END))
            
            # Read files efficiently
            file1_lines = self.read_file_efficient(self.file1_path.get())
            self.progress_var.set(25)
            
            file2_lines = self.read_file_efficient(self.file2_path.get())
            self.progress_var.set(50)
            
            # Compare files using unified_diff for better performance
            differ = difflib.Differ()
            self.diff_results = list(differ.compare(file1_lines, file2_lines))
            self.progress_var.set(75)
            
            # Update UI in the main thread
            self.root.after(0, self._update_comparison_display)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.compare_button.config(state=tk.NORMAL))
    
    def _update_comparison_display(self):
        """Update the display with comparison results"""
        batch_size = 1000  # Process lines in batches
        total_lines = len(self.diff_results)
        
        for i in range(0, total_lines, batch_size):
            batch = self.diff_results[i:i + batch_size]
            for line in batch:
                if line.startswith('  '):  # Unchanged
                    self.text_area1.insert(tk.END, line[2:])
                    self.text_area2.insert(tk.END, line[2:])
                elif line.startswith('- '):  # Removed
                    self.text_area1.insert(tk.END, line[2:], 'removed')
                elif line.startswith('+ '):  # Added
                    self.text_area2.insert(tk.END, line[2:], 'added')
            
            # Update progress
            progress = min(100, 75 + (i / total_lines) * 25)
            self.progress_var.set(progress)
            self.root.update_idletasks()
        
        # Configure tags for highlighting
        self.text_area1.tag_configure('removed', background='#ffcccb')
        self.text_area2.tag_configure('added', background='#90EE90')
        
        # Enable report button
        self.report_button.config(state=tk.NORMAL)
        self.progress_var.set(100)
    
    def format_json_threaded(self):
        """Start JSON formatting in a separate thread"""
        self.format_json_button.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._format_json_worker)
        thread.daemon = True
        thread.start()
    
    def _format_json_worker(self):
        """Worker function for JSON formatting"""
        try:
            # Format File 1
            if self.file1_path.get():
                content = self.read_file_efficient(self.file1_path.get())
                if content:
                    json_obj = json.loads(''.join(content))
                    formatted_json = json.dumps(json_obj, indent=4)
                    self.root.after(0, lambda: self._update_text_area(self.text_area1, formatted_json))
            
            # Format File 2
            if self.file2_path.get():
                content = self.read_file_efficient(self.file2_path.get())
                if content:
                    json_obj = json.loads(''.join(content))
                    formatted_json = json.dumps(json_obj, indent=4)
                    self.root.after(0, lambda: self._update_text_area(self.text_area2, formatted_json))
            
            self.root.after(0, lambda: messagebox.showinfo("Success", "JSON formatting complete!"))
            
        except json.JSONDecodeError as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Invalid JSON: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.format_json_button.config(state=tk.NORMAL))
    
    def _update_text_area(self, text_area, content):
        """Update text area content"""
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, content)
    
    def generate_report_threaded(self):
        """Start report generation in a separate thread"""
        self.report_button.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._generate_report_worker)
        thread.daemon = True
        thread.start()
    
    def _generate_report_worker(self):
        """Worker function for report generation"""
        try:
            if not self.diff_results:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please compare files first"))
                return
            
            # Create report content using StringIO for better performance
            with io.StringIO() as report:
                report.write("Text File Comparison Report\n")
                report.write("=" * 30 + "\n")
                report.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                report.write(f"File 1: {self.file1_path.get()}\n")
                report.write(f"JSON Status: {'Valid' if self.json_valid1 else 'Invalid'}\n\n")
                report.write(f"File 2: {self.file2_path.get()}\n")
                report.write(f"JSON Status: {'Valid' if self.json_valid2 else 'Invalid'}\n\n")
                report.write("Summary:\n")
                report.write("-" * 30 + "\n")
                
                # Count differences efficiently
                added = sum(1 for line in self.diff_results if line.startswith('+ '))
                removed = sum(1 for line in self.diff_results if line.startswith('- '))
                unchanged = sum(1 for line in self.diff_results if line.startswith('  '))
                
                report.write(f"Lines added: {added}\n")
                report.write(f"Lines removed: {removed}\n")
                report.write(f"Lines unchanged: {unchanged}\n\n")
                
                report.write("Detailed Differences:\n")
                report.write("-" * 30 + "\n")
                
                # Add detailed differences in batches
                batch_size = 1000
                for i in range(0, len(self.diff_results), batch_size):
                    batch = self.diff_results[i:i + batch_size]
                    for line in batch:
                        if line.startswith('+ '):
                            report.write(f"Added: {line[2:]}")
                        elif line.startswith('- '):
                            report.write(f"Removed: {line[2:]}")
                
                # Save report
                default_filename = f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                def save_report():
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Text Files", "*.txt")],
                        initialfile=default_filename
                    )
                    if filename:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(report.getvalue())
                        messagebox.showinfo("Success", f"Report saved successfully to:\n{filename}")
                
                self.root.after(0, save_report)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate report: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.report_button.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = TextFileComparator(root)
    root.mainloop() 