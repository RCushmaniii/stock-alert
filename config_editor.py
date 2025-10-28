"""
Config Editor - FreeSimpleGUI interface for editing config.json
Provides a visual form for managing stock alert settings
"""

import json
import os
import sys
import FreeSimpleGUI as sg
from utils.data_provider import DataProvider


class ConfigEditor:
    """Visual configuration editor using PySimpleGUI"""
    
    def __init__(self, config_path='config.json'):
        """
        Initialize config editor
        
        Args:
            config_path: Path to JSON configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.data_provider = DataProvider()
        
        # Set theme
        sg.theme('DarkBlue3')
    
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
            sg.popup_error(f"Error loading config: {e}")
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
            sg.popup_error(f"Error saving config: {e}")
            return False
    
    def create_settings_tab(self):
        """Create the global settings tab layout"""
        settings = self.config['settings']
        
        layout = [
            [sg.Text('Global Settings', font=('Helvetica', 16, 'bold'))],
            [sg.HorizontalSeparator()],
            [sg.Text('')],
            
            [sg.Text('Check Interval (seconds):', size=(25, 1)), 
             sg.Input(settings['check_interval'], key='check_interval', size=(10, 1)),
             sg.Text('How often to check stock prices')],
            
            [sg.Text('Cooldown Period (seconds):', size=(25, 1)), 
             sg.Input(settings['cooldown'], key='cooldown', size=(10, 1)),
             sg.Text('Time between repeated alerts')],
            
            [sg.Text('Notifications Enabled:', size=(25, 1)), 
             sg.Checkbox('', default=settings['notifications_enabled'], key='notifications_enabled'),
             sg.Text('Enable/disable toast notifications')],
            
            [sg.Text('')],
            [sg.Button('Save Settings', key='save_settings'), 
             sg.Text('', key='settings_status', size=(40, 1))]
        ]
        
        return layout
    
    def create_ticker_row(self, ticker, index):
        """Create a single ticker row for the table"""
        return [
            ticker.get('symbol', ''),
            ticker.get('name', ''),
            f"${ticker.get('high_threshold', 0):.2f}",
            f"${ticker.get('low_threshold', 0):.2f}",
            '✓' if ticker.get('enabled', True) else '✗'
        ]
    
    def create_tickers_tab(self):
        """Create the tickers management tab layout"""
        tickers = self.config['tickers']
        
        # Create table data
        table_data = [self.create_ticker_row(t, i) for i, t in enumerate(tickers)]
        
        headings = ['Symbol', 'Name', 'High Threshold', 'Low Threshold', 'Enabled']
        
        layout = [
            [sg.Text('Stock Tickers', font=('Helvetica', 16, 'bold'))],
            [sg.HorizontalSeparator()],
            [sg.Text('')],
            
            [sg.Table(
                values=table_data,
                headings=headings,
                auto_size_columns=True,
                display_row_numbers=False,
                justification='left',
                num_rows=min(10, len(table_data) + 1),
                key='ticker_table',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                expand_x=True,
                expand_y=True
            )],
            
            [sg.Text('')],
            [sg.Button('Add Ticker', key='add_ticker'),
             sg.Button('Edit Ticker', key='edit_ticker'),
             sg.Button('Delete Ticker', key='delete_ticker'),
             sg.Button('Toggle Enabled', key='toggle_ticker')]
        ]
        
        return layout
    
    def create_ticker_form_window(self, ticker=None, title='Add Ticker'):
        """Create a popup window for adding/editing a ticker"""
        is_edit = ticker is not None
        
        if ticker:
            symbol = ticker.get('symbol', '')
            name = ticker.get('name', '')
            high = ticker.get('high_threshold', 0.0)
            low = ticker.get('low_threshold', 0.0)
            enabled = ticker.get('enabled', True)
        else:
            symbol = ''
            name = ''
            high = 0.0
            low = 0.0
            enabled = True
        
        layout = [
            [sg.Text(title, font=('Helvetica', 14, 'bold'))],
            [sg.HorizontalSeparator()],
            [sg.Text('')],
            
            [sg.Text('Symbol:', size=(15, 1)), 
             sg.Input(symbol, key='symbol', size=(15, 1), disabled=is_edit),
             sg.Button('Validate', key='validate_symbol', disabled=is_edit)],
            
            [sg.Text('Name:', size=(15, 1)), 
             sg.Input(name, key='name', size=(30, 1))],
            
            [sg.Text('High Threshold:', size=(15, 1)), 
             sg.Input(high, key='high_threshold', size=(15, 1))],
            
            [sg.Text('Low Threshold:', size=(15, 1)), 
             sg.Input(low, key='low_threshold', size=(15, 1))],
            
            [sg.Text('Enabled:', size=(15, 1)), 
             sg.Checkbox('', default=enabled, key='enabled')],
            
            [sg.Text('')],
            [sg.Button('Save', key='save_ticker'), 
             sg.Button('Cancel', key='cancel_ticker'),
             sg.Text('', key='ticker_status', size=(30, 1))]
        ]
        
        return sg.Window(title, layout, modal=True, finalize=True)
    
    def validate_ticker_form(self, values):
        """Validate ticker form inputs"""
        errors = []
        
        symbol = values['symbol'].strip().upper()
        if not symbol:
            errors.append("Symbol is required")
        
        try:
            high = float(values['high_threshold'])
            if high <= 0:
                errors.append("High threshold must be positive")
        except ValueError:
            errors.append("High threshold must be a number")
            high = 0
        
        try:
            low = float(values['low_threshold'])
            if low <= 0:
                errors.append("Low threshold must be positive")
        except ValueError:
            errors.append("Low threshold must be a number")
            low = 0
        
        if not errors and high <= low:
            errors.append("High threshold must be greater than low threshold")
        
        return errors, {
            'symbol': symbol,
            'name': values['name'].strip() or symbol,
            'high_threshold': high,
            'low_threshold': low,
            'enabled': values['enabled']
        }
    
    def handle_add_ticker(self):
        """Handle adding a new ticker"""
        window = self.create_ticker_form_window()
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, 'cancel_ticker'):
                break
            
            if event == 'validate_symbol':
                symbol = values['symbol'].strip().upper()
                if symbol:
                    window['ticker_status'].update('Validating...', text_color='white')
                    window.refresh()
                    
                    if self.data_provider.validate_symbol(symbol):
                        window['ticker_status'].update('✓ Valid symbol', text_color='white')
                    else:
                        window['ticker_status'].update('✗ Invalid symbol', text_color='red')
                else:
                    window['ticker_status'].update('Enter a symbol first', text_color='white')
            
            if event == 'save_ticker':
                errors, ticker_data = self.validate_ticker_form(values)
                
                if errors:
                    sg.popup_error('Validation Errors:\n\n' + '\n'.join(errors))
                    continue
                
                # Check for duplicate
                if any(t['symbol'] == ticker_data['symbol'] for t in self.config['tickers']):
                    sg.popup_error(f"Ticker {ticker_data['symbol']} already exists")
                    continue
                
                self.config['tickers'].append(ticker_data)
                
                if self.save_config():
                    sg.popup('Ticker added successfully!')
                    break
        
        window.close()
    
    def handle_edit_ticker(self, index):
        """Handle editing an existing ticker"""
        if index < 0 or index >= len(self.config['tickers']):
            sg.popup_error('Please select a ticker to edit')
            return
        
        ticker = self.config['tickers'][index]
        window = self.create_ticker_form_window(ticker, 'Edit Ticker')
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, 'cancel_ticker'):
                break
            
            if event == 'save_ticker':
                errors, ticker_data = self.validate_ticker_form(values)
                
                if errors:
                    sg.popup_error('Validation Errors:\n\n' + '\n'.join(errors))
                    continue
                
                self.config['tickers'][index] = ticker_data
                
                if self.save_config():
                    sg.popup('Ticker updated successfully!')
                    break
        
        window.close()
    
    def handle_delete_ticker(self, index):
        """Handle deleting a ticker"""
        if index < 0 or index >= len(self.config['tickers']):
            sg.popup_error('Please select a ticker to delete')
            return
        
        ticker = self.config['tickers'][index]
        
        if sg.popup_yes_no(f"Delete ticker {ticker['symbol']}?") == 'Yes':
            del self.config['tickers'][index]
            
            if self.save_config():
                sg.popup('Ticker deleted successfully!')
    
    def handle_toggle_ticker(self, index):
        """Handle toggling ticker enabled status"""
        if index < 0 or index >= len(self.config['tickers']):
            sg.popup_error('Please select a ticker to toggle')
            return
        
        self.config['tickers'][index]['enabled'] = not self.config['tickers'][index].get('enabled', True)
        self.save_config()
    
    def update_ticker_table(self, window):
        """Update the ticker table display"""
        table_data = [self.create_ticker_row(t, i) for i, t in enumerate(self.config['tickers'])]
        window['ticker_table'].update(values=table_data)
    
    def run(self):
        """Run the configuration editor GUI"""
        # Create main window with tabs
        tab_settings = sg.Tab('Settings', self.create_settings_tab())
        tab_tickers = sg.Tab('Tickers', self.create_tickers_tab())
        
        layout = [
            [sg.Text('Stock Alert Configuration Editor', font=('Helvetica', 18, 'bold'))],
            [sg.HorizontalSeparator()],
            [sg.TabGroup([[tab_settings, tab_tickers]], key='tabs', expand_x=True, expand_y=True)],
            [sg.HorizontalSeparator()],
            [sg.Button('Exit', key='exit')]
        ]
        
        window = sg.Window(
            'Stock Alert Config Editor',
            layout,
            size=(800, 600),
            resizable=True,
            finalize=True
        )
        
        selected_row = -1
        
        while True:
            event, values = window.read()
            
            if event in (sg.WIN_CLOSED, 'exit'):
                break
            
            # Settings tab events
            if event == 'save_settings':
                try:
                    self.config['settings']['check_interval'] = int(values['check_interval'])
                    self.config['settings']['cooldown'] = int(values['cooldown'])
                    self.config['settings']['notifications_enabled'] = values['notifications_enabled']
                    
                    if self.save_config():
                        window['settings_status'].update('✓ Settings saved successfully!', text_color='white')
                    else:
                        window['settings_status'].update('✗ Failed to save settings', text_color='red')
                except ValueError:
                    window['settings_status'].update('✗ Invalid input values', text_color='red')
            
            # Tickers tab events
            if event == 'ticker_table':
                if values['ticker_table']:
                    selected_row = values['ticker_table'][0]
            
            if event == 'add_ticker':
                self.handle_add_ticker()
                self.update_ticker_table(window)
            
            if event == 'edit_ticker':
                if selected_row >= 0:
                    self.handle_edit_ticker(selected_row)
                    self.update_ticker_table(window)
                else:
                    sg.popup_error('Please select a ticker to edit')
            
            if event == 'delete_ticker':
                if selected_row >= 0:
                    self.handle_delete_ticker(selected_row)
                    self.update_ticker_table(window)
                    selected_row = -1
                else:
                    sg.popup_error('Please select a ticker to delete')
            
            if event == 'toggle_ticker':
                if selected_row >= 0:
                    self.handle_toggle_ticker(selected_row)
                    self.update_ticker_table(window)
                else:
                    sg.popup_error('Please select a ticker to toggle')
        
        window.close()


def main():
    """Entry point for config editor"""
    # Change to the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(app_dir)
    
    editor = ConfigEditor()
    editor.run()


if __name__ == "__main__":
    main()
