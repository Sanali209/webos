import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from parser import LogParser, LogEntry

SETTINGS_FILE = "settings.json"

class LogInspectorApp(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly", title="Log Inspector", size=(1200, 800))
        
        self.settings = self.load_settings()
        self.style.theme_use(self.settings.get("theme", "darkly"))
        
        self.log_parser = LogParser()
        self.monitored_files = self.settings.get("files", ["run_py.log"])
        self.file_positions: Dict[str, int] = {}
        self.is_monitoring = True
        self.log_entries: List[LogEntry] = []
        
        # UI Setup
        self.setup_ui()
        
        # Load existing files and start thread
        self.update_file_listbox()
        self.start_monitoring_thread()

    def load_settings(self) -> dict:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"theme": "darkly", "files": ["run_py.log"], "level_filter": "ALL"}

    def save_settings(self):
        self.settings["theme"] = self.style.theme.name
        self.settings["files"] = self.monitored_files
        self.settings["level_filter"] = self.level_var.get()
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)

    def setup_ui(self):
        # Main Layout: PanedWindow (Sidebar | Main Content)
        self.paned = tb.Panedwindow(self, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Sidebar
        self.sidebar_frame = tb.Frame(self.paned, padding=10)
        self.paned.add(self.sidebar_frame, weight=1)
        
        tb.Label(self.sidebar_frame, text="Log Inspector", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Files List
        tb.Label(self.sidebar_frame, text="Monitored Files:").pack(anchor=W, pady=(10,0))
        self.files_listbox = tk.Listbox(self.sidebar_frame, height=5)
        self.files_listbox.pack(fill=X, pady=5)
        
        file_btns = tb.Frame(self.sidebar_frame)
        file_btns.pack(fill=X)
        tb.Button(file_btns, text="Add", command=self.add_file, bootstyle="outline-primary").pack(side=LEFT, expand=True, fill=X, padx=2)
        tb.Button(file_btns, text="Remove", command=self.remove_file, bootstyle="outline-danger").pack(side=LEFT, expand=True, fill=X, padx=2)

        # Theme Selector
        tb.Label(self.sidebar_frame, text="Theme:").pack(anchor=W, pady=(15,0))
        self.theme_var = tb.StringVar(value=self.settings.get("theme", "darkly"))
        self.theme_combo = tb.Combobox(self.sidebar_frame, textvariable=self.theme_var, values=self.style.theme_names())
        self.theme_combo.pack(fill=X, pady=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # Level Filter
        tb.Label(self.sidebar_frame, text="Log Level:").pack(anchor=W, pady=(15,0))
        self.level_var = tb.StringVar(value=self.settings.get("level_filter", "ALL"))
        levels = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.level_combo = tb.Combobox(self.sidebar_frame, textvariable=self.level_var, values=levels)
        self.level_combo.pack(fill=X, pady=5)
        self.level_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_treeview())

        # Search / Regex Filter
        tb.Label(self.sidebar_frame, text="Search Regex:").pack(anchor=W, pady=(15,0))
        self.search_var = tb.StringVar()
        tb.Entry(self.sidebar_frame, textvariable=self.search_var).pack(fill=X, pady=5)
        self.search_var.trace_add("write", lambda *args: self.refresh_treeview())

        # Reset Logs Action
        tb.Button(self.sidebar_frame, text="Reset Logs", command=self.reset_logs, bootstyle="danger").pack(fill=X, pady=30)
        
        # Main Content (Treeview over Text Details)
        self.main_frame = tb.Frame(self.paned)
        self.paned.add(self.main_frame, weight=5)
        
        self.v_paned = tb.Panedwindow(self.main_frame, orient=VERTICAL)
        self.v_paned.pack(fill=BOTH, expand=True)

        # Treeview
        columns = ("Time", "Level", "Source", "Context", "Message")
        self.tree = tb.Treeview(self.v_paned, columns=columns, show="headings", bootstyle="primary")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150 if col != "Message" else 400)
            
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Tags for colors
        self.tree.tag_configure("ERROR", foreground="red")
        self.tree.tag_configure("CRITICAL", foreground="red")
        self.tree.tag_configure("WARNING", foreground="yellow")
        self.tree.tag_configure("INFO", foreground="white") # default text usually white/black depending on theme mapping, ttkbootstrap handles standard tags loosely
        self.v_paned.add(self.tree, weight=3)

        # Detail Text Area
        self.detail_text = tk.Text(self.v_paned, height=10, state="disabled")
        self.v_paned.add(self.detail_text, weight=1)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def change_theme(self, event):
        theme = self.theme_var.get()
        self.style.theme_use(theme)
        self.save_settings()

    def add_file(self):
        import tkinter.filedialog as fd
        # Look in project root typically
        files = fd.askopenfilenames(initialdir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), title="Select Log Files", filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        for file in files:
            # Try to store relative if it's in same tree, else absolute
            try:
                rel = os.path.relpath(file, start=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                fpath = rel
            except:
                fpath = file
                
            if fpath not in self.monitored_files:
                self.monitored_files.append(fpath)
        self.save_settings()
        self.update_file_listbox()
        # Initialize position
        for f in self.monitored_files:
            if f not in self.file_positions:
                self.file_positions[f] = 0

    def remove_file(self):
        selection = self.files_listbox.curselection()
        if selection:
            idx = selection[0]
            val = self.files_listbox.get(idx)
            self.monitored_files.remove(val)
            self.save_settings()
            self.update_file_listbox()

    def update_file_listbox(self):
        self.files_listbox.delete(0, END)
        for f in self.monitored_files:
            self.files_listbox.insert(END, f)
            if f not in self.file_positions:
                # To read from beginning on first open, set to 0
                self.file_positions[f] = 0

    def reset_logs(self):
        if messagebox.askyesno("Reset Logs", "Are you sure you want to completely clear the physical target log files and clear the view?"):
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            for fname in self.monitored_files:
                abs_path = os.path.join(root_dir, fname)
                if os.path.exists(abs_path):
                    with open(abs_path, 'w') as f:
                        f.truncate(0)
                self.file_positions[fname] = 0
            
            self.log_entries.clear()
            self.refresh_treeview()

    def start_monitoring_thread(self):
        self.monitor_thread = threading.Thread(target=self.tail_files, daemon=True)
        self.monitor_thread.start()

    def tail_files(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        while self.is_monitoring:
            new_entries = []
            for fname in self.monitored_files.copy():
                abs_path = os.path.join(root_dir, fname)
                if not os.path.exists(abs_path):
                    continue
                
                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                        pos = self.file_positions.get(fname, 0)
                        
                        f.seek(0, 2)
                        end_pos = f.tell()
                        
                        # If file got truncated (Reset Logs, or rotation)
                        if end_pos < pos:
                            pos = 0
                            
                        f.seek(pos)
                        lines = f.readlines()
                        self.file_positions[fname] = f.tell()
                        
                        for line in lines:
                            entry = self.log_parser.parse_line(line, fname)
                            if entry:
                                new_entries.append(entry)
                            elif self.log_entries and line.strip():
                                # It's a continuation of the previous log entry (like stack trace)
                                # For simplicity, append to the last one
                                self.log_entries[-1].message += "\n" + self.log_parser.clean_ansi(line).rstrip('\n')
                except Exception as e:
                    print(f"Error reading {fname}: {e}")
            
            if new_entries:
                self.log_entries.extend(new_entries)
                # Schedule GUI update
                self.after(0, lambda e=new_entries: self.add_to_treeview(e))
                
            time.sleep(0.5)

    def matches_filter(self, entry: LogEntry) -> bool:
        level = self.level_var.get()
        if level != "ALL" and level not in entry.level: # partial match logic
            return False
        
        search = self.search_var.get().lower()
        if search:
            import re
            try:
                if not re.search(search, entry.raw_text, re.IGNORECASE):
                    return False
            except re.error:
                # If invalid regex, fallback to simple string match
                if search not in entry.raw_text.lower():
                    return False
        return True

    def refresh_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        filtered = [e for e in self.log_entries if self.matches_filter(e)]
        self.add_to_treeview(filtered)

    def add_to_treeview(self, entries: List[LogEntry]):
        for e in entries:
            if not self.matches_filter(e):
                continue
            
            # Use level as tag for coloring
            tag = "INFO"
            if "ERROR" in e.level or "CRITICAL" in e.level or "FATAL" in e.level:
                tag = "ERROR"
            elif "WARN" in e.level:
                tag = "WARNING"
                
            # Limit message length for grid preview
            msg_preview = e.message.split('\n')[0][:100] + ("..." if len(e.message)>100 else "")
            
            self.tree.insert("", END, values=(e.time, e.level, e.source_file, e.context, msg_preview), tags=(tag,))
        
        # Auto-scroll to bottom if new items added
        if entries:
            children = self.tree.get_children()
            if children:
                self.tree.see(children[-1])

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected[0])
        values = item['values']
        if not values: return
        
        # values are (Time, Level, Source, Context, MessagePreview)
        # Find exact entry from our list
        # We rely on Time + Source + Context matching for this simpler lookup
        time_val, src_val, ctx_val = values[0], values[2], values[3]
        
        found = next((e for e in reversed(self.log_entries) if e.time == time_val and e.source_file == src_val and e.context == ctx_val), None)
        
        self.detail_text.configure(state="normal")
        self.detail_text.delete(1.0, END)
        
        if found:
            self.detail_text.insert(END, f"Time:   {found.time}\n")
            self.detail_text.insert(END, f"Level:  {found.level}\n")
            self.detail_text.insert(END, f"Source: {found.source_file}  |  Context: {found.context}\n")
            self.detail_text.insert(END, f"Extra:  {found.extra}\n")
            self.detail_text.insert(END, "-"*80 + "\n")
            self.detail_text.insert(END, found.message)
            
        self.detail_text.configure(state="disabled")

    def on_close(self):
        self.is_monitoring = False
        self.save_settings()
        self.destroy()

if __name__ == "__main__":
    app = LogInspectorApp()
    app.mainloop()
