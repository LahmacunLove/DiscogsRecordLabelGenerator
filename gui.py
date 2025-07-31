#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discogs Record Label Generator - GUI Application

Cross-platform graphical interface for configuring and running the Discogs Record Label Generator.
Built with tkinter for maximum compatibility across Windows, macOS, and Linux.

@author: ffx
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import subprocess
import queue
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config, get_config_path

class DiscogsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discogs Record Label Generator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
            if os.path.exists(icon_path):
                self.root.iconphoto(False, tk.PhotoImage(file=icon_path))
        except:
            pass  # No icon, that's fine
        
        # Load current configuration
        self.config = {}
        self.load_current_config()
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        # Processing state
        self.is_processing = False
        self.process = None
        
        # Create UI
        self.create_widgets()
        self.populate_fields()
        
        # Start message queue checker
        self.check_queue()
    
    def load_current_config(self):
        """Load current configuration from file"""
        try:
            self.config = load_config()
        except Exception as e:
            print(f"Could not load config: {e}")
            self.config = {
                "DISCOGS_USER_TOKEN": "",
                "LIBRARY_PATH": str(Path.home() / "DiscogsLibrary")
            }
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weight
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Discogs Record Label Generator", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Discogs Token
        ttk.Label(config_frame, text="Discogs API Token:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(config_frame, textvariable=self.token_var, show="*", width=50)
        token_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Show/Hide token button
        self.show_token = tk.BooleanVar()
        def toggle_token_visibility():
            token_entry.config(show="" if self.show_token.get() else "*")
        
        ttk.Checkbutton(config_frame, text="Show", variable=self.show_token, 
                       command=toggle_token_visibility).grid(row=0, column=2, padx=(5, 0))
        
        # Library Path
        ttk.Label(config_frame, text="Library Path:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.path_var = tk.StringVar()
        path_frame = ttk.Frame(config_frame)
        path_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        path_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(path_frame, textvariable=self.path_var).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(path_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1, padx=(5, 0))
        
        # Save Configuration Button
        ttk.Button(config_frame, text="Save Configuration", 
                  command=self.save_config).grid(row=2, column=1, pady=(10, 0))
        
        # Processing Options Section
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Mode selection
        self.mode_var = tk.StringVar(value="full")
        self.mode_var.trace('w', self.on_mode_change)  # Add callback for mode changes
        
        ttk.Radiobutton(options_frame, text="Full Sync (Complete Collection)", 
                       variable=self.mode_var, value="full").grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Development Mode (First 10 releases)", 
                       variable=self.mode_var, value="dev").grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Dry Run (Offline processing)", 
                       variable=self.mode_var, value="dryrun").grid(row=2, column=0, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Download Only (No analysis/labels)", 
                       variable=self.mode_var, value="download_only").grid(row=3, column=0, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Generate Labels Only (Combine existing LaTeX)", 
                       variable=self.mode_var, value="labels_only").grid(row=4, column=0, sticky=tk.W)
        
        # Custom limit
        limit_frame = ttk.Frame(options_frame)
        limit_frame.grid(row=5, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Radiobutton(limit_frame, text="Custom Limit:", 
                       variable=self.mode_var, value="custom").grid(row=0, column=0)
        self.limit_var = tk.StringVar(value="25")
        limit_entry = ttk.Entry(limit_frame, textvariable=self.limit_var, width=10)
        limit_entry.grid(row=0, column=1, padx=(5, 0))
        ttk.Label(limit_frame, text="releases").grid(row=0, column=2, padx=(5, 0))
        
        # Additional options
        self.regenerate_labels_var = tk.BooleanVar()
        self.regenerate_waveforms_var = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="Regenerate LaTeX Labels", 
                       variable=self.regenerate_labels_var).grid(row=6, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Checkbutton(options_frame, text="Regenerate Waveforms", 
                       variable=self.regenerate_waveforms_var).grid(row=7, column=0, sticky=tk.W)
        
        # Label generation options (only shown when labels_only mode is selected)
        self.labels_dev_var = tk.BooleanVar()
        self.labels_dev_check = ttk.Checkbutton(options_frame, text="Development mode (first 10 labels)", 
                                               variable=self.labels_dev_var)
        self.labels_dev_check.grid(row=8, column=0, sticky=tk.W, pady=(5, 0))
        
        # Initially hide label-specific options
        self.labels_dev_check.grid_remove()
        
        # Control Buttons Section
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Processing", 
                                      command=self.start_processing, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(control_frame, text="Open Output Folder", 
                  command=self.open_output_folder).grid(row=0, column=2)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           mode="indeterminate")
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log output
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=15, width=80)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main grid weights
        main_frame.rowconfigure(4, weight=1)
    
    def on_mode_change(self, *args):
        """Handle mode selection changes to show/hide relevant options"""
        mode = self.mode_var.get()
        if mode == "labels_only":
            # Show label-specific options
            self.labels_dev_check.grid()
        else:
            # Hide label-specific options
            self.labels_dev_check.grid_remove()
    
    def populate_fields(self):
        """Populate fields with current configuration"""
        self.token_var.set(self.config.get("DISCOGS_USER_TOKEN", ""))
        self.path_var.set(self.config.get("LIBRARY_PATH", ""))
    
    def browse_folder(self):
        """Browse for library folder"""
        folder = filedialog.askdirectory(
            title="Select Library Folder",
            initialdir=self.path_var.get() or str(Path.home())
        )
        if folder:
            self.path_var.set(folder)
    
    def save_config(self):
        """Save configuration to file"""
        if not self.token_var.get().strip():
            messagebox.showerror("Error", "Discogs API Token is required!")
            return
        
        if not self.path_var.get().strip():
            messagebox.showerror("Error", "Library Path is required!")
            return
        
        # Create config directory if it doesn't exist
        config_path = get_config_path()
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)
        
        # Prepare config data
        config_data = {
            "DISCOGS_USER_TOKEN": self.token_var.get().strip(),
            "LIBRARY_PATH": self.path_var.get().strip()
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            self.config = config_data
            messagebox.showinfo("Success", f"Configuration saved to:\n{config_path}")
            self.log_message("✅ Configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")
    
    def start_processing(self):
        """Start the processing in a separate thread"""
        if not self.validate_config():
            return
        
        # Save config before starting
        self.save_config()
        
        # Build command
        mode = self.mode_var.get()
        
        if mode == "labels_only":
            # Use generate_labels.py for labels-only mode
            cmd = [sys.executable, "generate_labels.py"]
            
            # Add development mode for labels if selected
            if self.labels_dev_var.get():
                cmd.append("--dev")
            
        else:
            # Use main.py for all other modes
            cmd = [sys.executable, "main.py"]
            
            # Add GUI mode for progress reporting (for full sync only)
            if mode == "full":
                cmd.append("--gui-mode")
            
            if mode == "dev":
                cmd.append("--dev")
            elif mode == "dryrun":
                cmd.append("--dryrun")
            elif mode == "download_only":
                cmd.append("--download-only")
            elif mode == "custom":
                try:
                    limit = int(self.limit_var.get())
                    cmd.extend(["--max", str(limit)])
                except ValueError:
                    messagebox.showerror("Error", "Custom limit must be a number!")
                    return
            
            if self.regenerate_labels_var.get():
                cmd.append("--regenerate-labels")
            
            if self.regenerate_waveforms_var.get():
                cmd.append("--regenerate-waveforms")
        
        # Clear log and start processing
        self.log_text.delete(1.0, tk.END)
        self.log_message(f"🚀 Starting: {' '.join(cmd)}")
        
        # Update UI state
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Set progress bar mode based on whether we expect progress updates
        if mode == "full" and not (self.regenerate_labels_var.get() or self.regenerate_waveforms_var.get()):
            # Full sync mode - use determinate progress bar
            self.progress_bar.config(mode="determinate")
            self.progress_var.set(0)
        else:
            # Other modes - use indeterminate progress bar
            self.progress_bar.config(mode="indeterminate")
            self.progress_bar.start()
        
        # Start processing thread
        thread = threading.Thread(target=self.run_processing, args=(cmd,))
        thread.daemon = True
        thread.start()
    
    def run_processing(self, cmd):
        """Run the processing command"""
        try:
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=os.path.dirname(__file__)
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_processing:  # Check if we should stop
                    break
                
                line = line.rstrip()
                
                # Check for progress updates
                if line.startswith('GUI_PROGRESS:'):
                    self.message_queue.put(('progress', line))
                else:
                    self.message_queue.put(('log', line))
            
            # Wait for process to complete
            return_code = self.process.wait()
            
            if return_code == 0:
                self.message_queue.put(('success', "✅ Processing completed successfully!"))
            else:
                self.message_queue.put(('error', f"❌ Processing failed with exit code {return_code}"))
                
        except Exception as e:
            self.message_queue.put(('error', f"❌ Error running process: {e}"))
        finally:
            self.message_queue.put(('finished', None))
    
    def stop_processing(self):
        """Stop the current processing"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log_message("🛑 Processing stopped by user")
        
        self.processing_finished()
    
    def processing_finished(self):
        """Reset UI after processing is finished"""
        self.is_processing = False
        self.process = None
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate")
        self.progress_var.set(0)
    
    def validate_config(self):
        """Validate configuration before starting"""
        if not self.token_var.get().strip():
            messagebox.showerror("Error", "Please enter your Discogs API Token!")
            return False
        
        if not self.path_var.get().strip():
            messagebox.showerror("Error", "Please select a Library Path!")
            return False
        
        # Validate path exists or can be created
        try:
            path = Path(self.path_var.get().strip()).expanduser()
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create library path:\n{e}")
            return False
            
        return True
    
    def open_output_folder(self):
        """Open the output folder in file manager"""
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("Warning", "No library path configured!")
            return
        
        path = Path(path).expanduser()
        if not path.exists():
            messagebox.showwarning("Warning", "Library path does not exist yet!")
            return
        
        # Open folder in OS-specific way
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:  # Linux and others
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")
    
    def log_message(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def handle_progress_update(self, message):
        """Handle progress update from subprocess"""
        try:
            # Parse: "GUI_PROGRESS: 45.2% (5/11) - Processing releases"
            if message.startswith('GUI_PROGRESS:'):
                progress_part = message.split(':', 1)[1].strip()
                percentage_part = progress_part.split('%')[0].strip()
                percentage = float(percentage_part)
                
                # Update progress bar
                self.progress_var.set(percentage)
                
                # Also log the progress message
                self.log_message(f"📊 {progress_part}")
                
        except (ValueError, IndexError) as e:
            # If parsing fails, just log the original message
            self.log_message(message)
    
    def check_queue(self):
        """Check message queue for updates from processing thread"""
        try:
            while True:
                msg_type, message = self.message_queue.get_nowait()
                
                if msg_type == 'log':
                    self.log_message(message)
                elif msg_type == 'progress':
                    self.handle_progress_update(message)
                elif msg_type == 'success' or msg_type == 'error':
                    self.log_message(message)
                elif msg_type == 'finished':
                    self.processing_finished()
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_queue)

def main():
    """Main GUI entry point"""
    # Create root window
    root = tk.Tk()
    
    # Try to set a nice theme
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass  # Theme not available, use default
    
    # Create and run GUI
    app = DiscogsGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Start GUI
    root.mainloop()

if __name__ == "__main__":
    main()