"""
Config Editor - Tkinter interface for editing config.json
Provides a visual form for managing stock alert settings using built-in Tkinter
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from utils.data_provider import DataProvider


class ConfigEditor:
    """Visual configuration editor using Tkinter"""
    
    def __init__(self, config_path='config.json'):
        """
        Initialize config editor
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.data_provider = DataProvider()
        
        self.root = tk.Tk()
        self.root.title("Stock Alert Configuration Editor")
        self.root.geometry("900x600")
        
        self.create_ui()
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(self.config_path):
                # Create from example if available
                example_path = 'config.example.json'
                if os.path.exists(example_path):
                    with open(example_path, 'r') as f:
                        config = json.load(f)
                    self.save_config(config)
                    return config
                else:
                    # Create default config
                    return self.create_default_config()
            
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading config: {e}")
            return self.create_default_config()
    
    def create_default_config(self):
        """Create a default configuration"""
        return {
            "settings": {
                "check_interval": 60,
                "cooldown": 300,
                "notifications_enabled": True
            },
            "tickers": []
        }
    
    def save_config(self, config=None):
        """Save configuration to JSON file"""
        try:
            if config is None:
                config = self.config
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error saving config: {e}")
            return False
    
    def create_ui(self):
        """Create the main UI"""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text='Settings')
        self.create_settings_tab(settings_frame)
        
        # Tickers tab
        tickers_frame = ttk.Frame(notebook)
        notebook.add(tickers_frame, text='Tickers')
        self.create_tickers_tab(tickers_frame)
    
    def create_settings_tab(self, parent):
        """Create the global settings tab"""
        settings = self.config['settings']
        
        # Title
        title = ttk.Label(parent, text="Global Settings", font=('Helvetica', 16, 'bold'))
        title.pack(pady=10)
        
        # Settings frame
        frame = ttk.Frame(parent)
        frame.pack(padx=20, pady=10, fill='x')
        
        # Check interval
        ttk.Label(frame, text="Check Interval (seconds):").grid(row=0, column=0, sticky='w', pady=5)
        self.check_interval_var = tk.StringVar(value=str(settings['check_interval']))
        ttk.Entry(frame, textvariable=self.check_interval_var, width=15).grid(row=0, column=1, sticky='w', padx=10)
        ttk.Label(frame, text="How often to check stock prices").grid(row=0, column=2, sticky='w', padx=10)
        
        # Cooldown
        ttk.Label(frame, text="Cooldown Period (seconds):").grid(row=1, column=0, sticky='w', pady=5)
        self.cooldown_var = tk.StringVar(value=str(settings['cooldown']))
        ttk.Entry(frame, textvariable=self.cooldown_var, width=15).grid(row=1, column=1, sticky='w', padx=10)
        ttk.Label(frame, text="Time between repeated alerts").grid(row=1, column=2, sticky='w', padx=10)
        
        # Notifications enabled
        ttk.Label(frame, text="Notifications Enabled:").grid(row=2, column=0, sticky='w', pady=5)
        self.notifications_var = tk.BooleanVar(value=settings['notifications_enabled'])
        ttk.Checkbutton(frame, variable=self.notifications_var).grid(row=2, column=1, sticky='w', padx=10)
        ttk.Label(frame, text="Enable/disable toast notifications").grid(row=2, column=2, sticky='w', padx=10)
        
        # Save button
        save_btn = ttk.Button(frame, text="Save Settings", command=self.save_settings)
        save_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Status label
        self.settings_status = ttk.Label(frame, text="", foreground="green")
        self.settings_status.grid(row=3, column=2, sticky='w', padx=10)
    
    def save_settings(self):
        """Save global settings"""
        try:
            self.config['settings']['check_interval'] = int(self.check_interval_var.get())
            self.config['settings']['cooldown'] = int(self.cooldown_var.get())
            self.config['settings']['notifications_enabled'] = self.notifications_var.get()
            
            if self.save_config():
                self.settings_status.config(text="✓ Settings saved!", foreground="green")
                self.root.after(3000, lambda: self.settings_status.config(text=""))
        except ValueError:
            messagebox.showerror("Error", "Invalid input values. Please enter numbers for intervals.")
    
    def create_tickers_tab(self, parent):
        """Create the tickers management tab"""
        # Title
        title = ttk.Label(parent, text="Stock Tickers", font=('Helvetica', 16, 'bold'))
        title.pack(pady=10)
        
        # Treeview frame
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        columns = ('Symbol', 'Name', 'High Threshold', 'Low Threshold', 'Enabled')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        self.tree.pack(fill='both', expand=True)
        
        # Populate tree
        self.refresh_ticker_list()
        
        # Buttons frame
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Add Ticker", command=self.add_ticker).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Edit Ticker", command=self.edit_ticker).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete Ticker", command=self.delete_ticker).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Toggle Enabled", command=self.toggle_ticker).pack(side='left', padx=5)
    
    def refresh_ticker_list(self):
        """Refresh the ticker list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add tickers
        for ticker in self.config['tickers']:
            self.tree.insert('', 'end', values=(
                ticker['symbol'],
                ticker.get('name', ticker['symbol']),
                f"${ticker['high_threshold']:.2f}",
                f"${ticker['low_threshold']:.2f}",
                '✓' if ticker.get('enabled', True) else '✗'
            ))
    
    def add_ticker(self):
        """Add a new ticker"""
        dialog = TickerDialog(self.root, "Add Ticker", self.data_provider)
        if dialog.result:
            # Check for duplicate
            if any(t['symbol'] == dialog.result['symbol'] for t in self.config['tickers']):
                messagebox.showerror("Error", f"Ticker {dialog.result['symbol']} already exists")
                return
            
            self.config['tickers'].append(dialog.result)
            if self.save_config():
                self.refresh_ticker_list()
                messagebox.showinfo("Success", "Ticker added successfully!")
    
    def edit_ticker(self):
        """Edit selected ticker"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a ticker to edit")
            return
        
        index = self.tree.index(selection[0])
        ticker = self.config['tickers'][index]
        
        dialog = TickerDialog(self.root, "Edit Ticker", self.data_provider, ticker)
        if dialog.result:
            self.config['tickers'][index] = dialog.result
            if self.save_config():
                self.refresh_ticker_list()
                messagebox.showinfo("Success", "Ticker updated successfully!")
    
    def delete_ticker(self):
        """Delete selected ticker"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a ticker to delete")
            return
        
        index = self.tree.index(selection[0])
        ticker = self.config['tickers'][index]
        
        if messagebox.askyesno("Confirm", f"Delete ticker {ticker['symbol']}?"):
            del self.config['tickers'][index]
            if self.save_config():
                self.refresh_ticker_list()
                messagebox.showinfo("Success", "Ticker deleted successfully!")
    
    def toggle_ticker(self):
        """Toggle enabled status of selected ticker"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a ticker to toggle")
            return
        
        index = self.tree.index(selection[0])
        self.config['tickers'][index]['enabled'] = not self.config['tickers'][index].get('enabled', True)
        
        if self.save_config():
            self.refresh_ticker_list()
    
    def run(self):
        """Run the configuration editor"""
        self.root.mainloop()


class TickerDialog:
    """Dialog for adding/editing a ticker"""
    
    def __init__(self, parent, title, data_provider, ticker=None):
        self.result = None
        self.data_provider = data_provider
        self.is_edit = ticker is not None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create form
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill='both', expand=True)
        
        # Symbol
        ttk.Label(frame, text="Symbol:").grid(row=0, column=0, sticky='w', pady=5)
        self.symbol_var = tk.StringVar(value=ticker['symbol'] if ticker else '')
        symbol_entry = ttk.Entry(frame, textvariable=self.symbol_var, width=20)
        symbol_entry.grid(row=0, column=1, sticky='w', padx=10)
        if self.is_edit:
            symbol_entry.config(state='disabled')
        
        validate_btn = ttk.Button(frame, text="Validate", command=self.validate_symbol)
        validate_btn.grid(row=0, column=2, padx=5)
        if self.is_edit:
            validate_btn.config(state='disabled')
        
        # Name
        ttk.Label(frame, text="Name:").grid(row=1, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=ticker.get('name', '') if ticker else '')
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=1, column=1, columnspan=2, sticky='w', padx=10)
        
        # High threshold
        ttk.Label(frame, text="High Threshold:").grid(row=2, column=0, sticky='w', pady=5)
        self.high_var = tk.StringVar(value=str(ticker['high_threshold']) if ticker else '0.0')
        ttk.Entry(frame, textvariable=self.high_var, width=20).grid(row=2, column=1, sticky='w', padx=10)
        
        # Low threshold
        ttk.Label(frame, text="Low Threshold:").grid(row=3, column=0, sticky='w', pady=5)
        self.low_var = tk.StringVar(value=str(ticker['low_threshold']) if ticker else '0.0')
        ttk.Entry(frame, textvariable=self.low_var, width=20).grid(row=3, column=1, sticky='w', padx=10)
        
        # Enabled
        ttk.Label(frame, text="Enabled:").grid(row=4, column=0, sticky='w', pady=5)
        self.enabled_var = tk.BooleanVar(value=ticker.get('enabled', True) if ticker else True)
        ttk.Checkbutton(frame, variable=self.enabled_var).grid(row=4, column=1, sticky='w', padx=10)
        
        # Status label
        self.status_label = ttk.Label(frame, text="")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side='left', padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def validate_symbol(self):
        """Validate stock symbol"""
        symbol = self.symbol_var.get().strip().upper()
        if not symbol:
            self.status_label.config(text="Enter a symbol first", foreground="orange")
            return
        
        self.status_label.config(text="Validating...", foreground="blue")
        self.dialog.update()
        
        if self.data_provider.validate_symbol(symbol):
            self.status_label.config(text="✓ Valid symbol", foreground="green")
        else:
            self.status_label.config(text="✗ Invalid symbol", foreground="red")
    
    def save(self):
        """Save ticker data"""
        try:
            symbol = self.symbol_var.get().strip().upper()
            if not symbol:
                messagebox.showerror("Error", "Symbol is required")
                return
            
            high = float(self.high_var.get())
            low = float(self.low_var.get())
            
            if high <= 0 or low <= 0:
                messagebox.showerror("Error", "Thresholds must be positive")
                return
            
            if high <= low:
                messagebox.showerror("Error", "High threshold must be greater than low threshold")
                return
            
            self.result = {
                'symbol': symbol,
                'name': self.name_var.get().strip() or symbol,
                'high_threshold': high,
                'low_threshold': low,
                'enabled': self.enabled_var.get()
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid threshold values. Please enter numbers.")


def main():
    """Entry point for config editor"""
    editor = ConfigEditor()
    editor.run()


if __name__ == "__main__":
    main()
