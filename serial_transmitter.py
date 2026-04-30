"""
Serial Port Tester - A comprehensive serial communication testing tool
Version: 2.0.0
Author: Advantechnique

This application provides a GUI for testing serial port communications
with support for transmit, receive, and command modes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import threading
import logging
from datetime import datetime
import serial.tools.list_ports
import os
import json
import queue
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME = "Serial Port Tester"
APP_VERSION = "2.0.0"
CONFIG_FILE = "serial_tester_config.json"
LOG_FILE = "serial_transmission.log"

# Default configuration
DEFAULT_CONFIG = {
    "com_port": "",
    "baud_rate": 9600,
    "parity": "None",
    "data_bits": 8,
    "stop_bits": "One",
    "base_weight": 5555,
    "mode": "transmit",
    "selected_command": "IP",
    "custom_command": "",
    "delay_time": 1000,
    "auto_reconnect": False,
    "reconnect_interval": 5000,
    "log_to_file": True,
    "show_timestamps": True,
    "window_geometry": "600x700",
    "recent_commands": [],
    "max_recent_commands": 10
}

# Command definitions with descriptions
COMMAND_DEFINITIONS = {
    "@": "Reset the scale",
    "I0": "Inquiry of all available SICS commands",
    "I1": "Inquiry of SICS level and SICS versions",
    "I2": "Inquiry of scale data",
    "I3": "Inquiry of scale software version",
    "I4": "Inquiry of serial number",
    "I10": "Inquire or set scale ID",
    "I11": "Inquire of scale type",
    "S": "Send stable weight value",
    "SI": "Send weight value immediately",
    "SIR": "Send weight value repeatedly",
    "Z": "Zero the scale",
    "ZI": "Zero immediately",
    "D": "Write text into display",
    "DW": "Weight display",
    "SR": "Send and repeat stable weight value",
    "T": "Tare",
    "TA": "Tare value",
    "TAC": "Clear tare",
    "TI": "Tare immediately",
    "C2": "Calibrate with the external calibration weight",
    "C3": "Calibrate with the internal calibration weight",
    "P100": "Print out on the printer",
    "P101": "Print out stable weight value",
    "P102": "Print out current weight value immediately",
    "SIRU": "Send weight value in the current unit immediately and repeat",
    "SIU": "Send weight value in the current unit immediately",
    "SNR": "Send stable weight value and repeat after every weight change",
    "SNRU": "Send stable weight value in the current unit and repeat after every weight change",
    "SRU": "Send weight value in the current unit and repeat",
    "ST": "After pressing the Transfer key, send the stable weight value",
    "SU": "Send stable weight value in the current unit",
    "LST": "Send menu settings",
    "M01": "Weighing mode",
    "M02": "Stability setting",
    "M03": "Autozero function",
    "M19": "Send calibration weight",
    "M21": "Inquire/set weight unit",
    "P": "Print text",
    "PRN": "Print out at every printer interface",
    "RST": "Restart",
    "SFIR": "Send weight value immediately and repeat quickly",
    "SIH": "Send weight value immediately in high resolution",
    "SWU": "Switch weight unit",
    "SX": "Send stable data record",
    "SXI": "Send data record immediately",
    "SXIR": "Send data record immediately and repeat",
    "U": "Switch weight unit",
    "IP": "Initialize/Identification - Query device identity",
    "CP": "Clear Print - Clear print buffer",
    "SP": "Set Parameters - Configure device parameters",
    "xS": "Set Unit/Scale - Configure measurement unit",
    "xP": "Set Precision - Set decimal precision",
    "xT": "Set Tare - Configure tare value",
    "PU": "Print Unit - Print current unit",
    "xU": "Set Unit - Set measurement unit",
    "xM": "Set Mode - Change device mode",
    "PV": "Print Value - Print current value",
    "Esc R": "Escape Response - Reset/Response command"
}

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_to_file: bool = True):
    """Configure application logging with rotation."""
    handlers = [logging.StreamHandler()]
    
    if log_to_file:
        # Rotating file handler - 5MB max, keep 3 backups
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SerialConfig:
    """Serial port configuration data class."""
    com_port: str = ""
    baud_rate: int = 9600
    parity: str = "None"
    data_bits: int = 8
    stop_bits: str = "One"
    
    def to_serial_params(self) -> Dict[str, Any]:
        """Convert to pyserial parameters."""
        parity_map = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD
        }
        stop_bits_map = {
            "One": serial.STOPBITS_ONE,
            "Two": serial.STOPBITS_TWO
        }
        
        return {
            "port": self.com_port,
            "baudrate": self.baud_rate,
            "parity": parity_map.get(self.parity, serial.PARITY_NONE),
            "bytesize": self.data_bits,
            "stopbits": stop_bits_map.get(self.stop_bits, serial.STOPBITS_ONE),
            "timeout": 1,
            "write_timeout": 2
        }

# ============================================================================
# TOOLTIP CLASS
# ============================================================================

class ToolTip:
    """Create a tooltip for a given widget."""
    
    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)
    
    def _schedule(self, event=None):
        """Schedule tooltip display."""
        self.after_id = self.widget.after(self.delay, self._show)
    
    def _show(self):
        """Display the tooltip."""
        if self.tooltip_window:
            return
            
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffd0",
            foreground="#333333",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            padx=5,
            pady=3
        )
        label.pack()
    
    def _hide(self, event=None):
        """Hide the tooltip."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# ============================================================================
# SERIAL CONNECTION MANAGER
# ============================================================================

class SerialConnectionManager:
    """Manages serial port connections with thread safety."""
    
    def __init__(self):
        self._serial: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if serial port is connected."""
        with self._lock:
            return self._is_connected and self._serial is not None and self._serial.is_open
    
    @contextmanager
    def get_connection(self):
        """Context manager for thread-safe serial access."""
        with self._lock:
            yield self._serial
    
    def connect(self, config: SerialConfig) -> tuple[bool, str]:
        """
        Connect to serial port with given configuration.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        with self._lock:
            try:
                # Close existing connection if any
                if self._serial and self._serial.is_open:
                    self._serial.close()
                
                # Validate port availability
                if not config.com_port:
                    return False, "No COM port specified"
                
                available_ports = [p.device for p in serial.tools.list_ports.comports()]
                if config.com_port not in available_ports:
                    return False, f"Port {config.com_port} not found. Available: {', '.join(available_ports) or 'None'}"
                
                # Open new connection
                params = config.to_serial_params()
                self._serial = serial.Serial(**params)
                
                # Test connection with empty write
                self._serial.write(b"")
                self._serial.flush()
                
                self._is_connected = True
                return True, f"Connected to {config.com_port} at {config.baud_rate} baud"
                
            except PermissionError:
                self._is_connected = False
                return False, f"Access denied to {config.com_port}. Port may be in use by another application."
            except serial.SerialException as e:
                self._is_connected = False
                return False, f"Serial error: {str(e)}"
            except Exception as e:
                self._is_connected = False
                return False, f"Unexpected error: {str(e)}"
    
    def disconnect(self) -> tuple[bool, str]:
        """
        Disconnect from serial port.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        with self._lock:
            try:
                if self._serial and self._serial.is_open:
                    self._serial.close()
                self._is_connected = False
                return True, "Disconnected successfully"
            except Exception as e:
                return False, f"Error disconnecting: {str(e)}"
    
    def write(self, data: bytes) -> tuple[int, str]:
        """
        Write data to serial port.
        
        Returns:
            tuple: (bytes_written: int, error_message: str or None)
        """
        with self._lock:
            if not self._serial or not self._serial.is_open:
                return 0, "Port not open"
            
            try:
                written = self._serial.write(data)
                self._serial.flush()
                return written, ""
            except Exception as e:
                return 0, str(e)
    
    def read_line(self) -> tuple[bytes, str]:
        """
        Read data from serial port with multiple methods.
        
        Returns:
            tuple: (data: bytes, error: str)
        """
        with self._lock:
            if not self._serial or not self._serial.is_open:
                return b"", "Port not open"
            
            try:
                if self._serial.in_waiting > 0:
                    # Try to read all available data first
                    data = self._serial.read(self._serial.in_waiting)
                    
                    # If no data read, try readline as fallback
                    if not data:
                        data = self._serial.readline()
                    
                    return data, ""
                return b"", ""
            except Exception as e:
                return b"", str(e)
    
    def get_in_waiting(self) -> int:
        """Get number of bytes waiting in input buffer."""
        with self._lock:
            if self._serial and self._serial.is_open:
                return self._serial.in_waiting
            return 0

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class SerialTransmitterApp:
    """Main application class for Serial Port Tester."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(DEFAULT_CONFIG["window_geometry"])
        self.root.resizable(True, True)
        
        # Set minimum window size
        self.root.minsize(550, 600)
        
        # Set window icon if available
        try:
            import sys
            # Handle both running as script and compiled EXE
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                icon_path = os.path.join(sys._MEIPASS, "RS232.ico")
            else:
                # Running as normal Python script
                icon_path = os.path.join(os.path.dirname(__file__), "RS232.ico")
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                
                # Fix Windows taskbar icon issue: Set explicit App User Model ID
                # This tells Windows to use our application icon instead of default Python icon
                if sys.platform == 'win32':
                    import ctypes
                    # AppUserModelID should be unique for this application
                    app_id = f"{APP_NAME}.{APP_VERSION}".replace(" ", "")
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass
        
        # Initialize connection manager
        self.connection = SerialConnectionManager()
        
        # Threading synchronization
        self._operation_lock = threading.Lock()
        self._operation_queue = queue.Queue()
        self._operation_thread = None
        self._operations_running = False
        
        # Application watchdog for freeze prevention
        self._last_watchdog_update = time.time()
        self._watchdog_active = True
        
        # Threading control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._receive_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._message_queue = queue.Queue()
        
                
        # Load saved configuration
        self.config = self._load_config()
        
        # Command history
        self.recent_commands: List[str] = self.config.get("recent_commands", [])
        
        # Build UI
        self._setup_ui()
        
        # Auto-refresh COM ports on startup
        self._refresh_com_ports()
        self._setup_tooltips()
        self._setup_keyboard_shortcuts()
        
        # Start message pump for thread-safe GUI updates
        self._process_message_queue()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Status bar update
        self._update_connection_indicator()
    
    # ========================================================================
    # CONFIGURATION MANAGEMENT
    # ========================================================================
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    return {**DEFAULT_CONFIG, **loaded}
        except Exception as e:
            logging.warning(f"Could not load config: {e}")
        return DEFAULT_CONFIG.copy()
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save config: {e}")
    
    # ========================================================================
    # UI SETUP
    # ========================================================================
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Configure style
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 11, "bold"))
        style.configure("Status.TLabel", font=("Arial", 10))
        style.configure("Action.TButton", font=("Arial", 10, "bold"))
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar + Main content layout
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Left Sidebar: Serial Configuration + Controls stacked vertically
        sidebar_frame = ttk.Frame(content_frame)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # Top of sidebar: Serial Configuration
        self._setup_settings_frame(sidebar_frame)
        
        # Bottom of sidebar: Controls
        self._setup_control_frame(sidebar_frame)
        
        # Right Main area: Communication Log (full width & height)
        self._setup_log_frame(content_frame)
        
        # Status section at very bottom
        self._setup_status_frame(main_frame)
        
        # Mode-specific initial setup
        self._on_mode_change()
    
    def _setup_settings_frame(self, parent):
        """Set up the settings frame."""
        settings_frame = ttk.LabelFrame(parent, text="Serial Configuration", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 5))
        
        row = 0
        
        # --- COM Port ---
        ttk.Label(settings_frame, text="COM Port:").grid(row=row, column=0, sticky="w", pady=3)
        self.com_var = tk.StringVar(value=self.config.get("com_port", ""))
        self.com_combo = ttk.Combobox(settings_frame, textvariable=self.com_var, width=15, state="readonly")
        self.com_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        self.com_combo['values'] = self._get_com_ports()
        
        refresh_btn = ttk.Button(settings_frame, text="🔄", width=3, command=self._refresh_com_ports)
        refresh_btn.grid(row=row, column=2, padx=2, pady=3)
        row += 1
        
        # --- Baud Rate ---
        ttk.Label(settings_frame, text="Baud Rate:").grid(row=row, column=0, sticky="w", pady=3)
        baud_values = [300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]
        self.baud_var = tk.StringVar(value=str(self.config.get("baud_rate", 9600)))
        self.baud_combo = ttk.Combobox(settings_frame, textvariable=self.baud_var, values=baud_values, width=15)
        self.baud_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        self.baud_combo.bind("<<ComboboxSelected>>", self._on_baudrate_change)
        row += 1
        
        # --- Parity ---
        ttk.Label(settings_frame, text="Parity:").grid(row=row, column=0, sticky="w", pady=3)
        parity_values = ["None", "Even", "Odd"]
        self.parity_var = tk.StringVar(value=self.config.get("parity", "None"))
        self.parity_combo = ttk.Combobox(settings_frame, textvariable=self.parity_var, values=parity_values, width=15)
        self.parity_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        row += 1
        
        # --- Data Bits ---
        ttk.Label(settings_frame, text="Data Bits:").grid(row=row, column=0, sticky="w", pady=3)
        data_bits_values = [5, 6, 7, 8]
        self.data_bits_var = tk.StringVar(value=str(self.config.get("data_bits", 8)))
        self.data_bits_combo = ttk.Combobox(settings_frame, textvariable=self.data_bits_var, values=data_bits_values, width=15)
        self.data_bits_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        row += 1
        
        # --- Stop Bits ---
        ttk.Label(settings_frame, text="Stop Bits:").grid(row=row, column=0, sticky="w", pady=3)
        stop_bits_values = ["One", "Two"]
        self.stop_bits_var = tk.StringVar(value=self.config.get("stop_bits", "One"))
        self.stop_bits_combo = ttk.Combobox(settings_frame, textvariable=self.stop_bits_var, values=stop_bits_values, width=15)
        self.stop_bits_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        row += 1
        
        # --- Separator ---
        ttk.Separator(settings_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1
        
        # --- Mode ---
        ttk.Label(settings_frame, text="Mode:", style="Header.TLabel").grid(row=row, column=0, sticky="w", pady=3)
        mode_values = ["transmit", "receive", "command"]
        self.mode_var = tk.StringVar(value=self.config.get("mode", "transmit"))
        self.mode_combo = ttk.Combobox(settings_frame, textvariable=self.mode_var, values=mode_values, width=15, state="readonly")
        self.mode_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=3)
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)
        row += 1
        
        # --- Mode-specific controls container ---
        self.mode_frame = ttk.Frame(settings_frame)
        self.mode_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
        row += 1
        
        # Transmit mode: Base Weight
        self.weight_frame = ttk.Frame(self.mode_frame)
        ttk.Label(self.weight_frame, text="Base Weight:").pack(side=tk.LEFT)
        self.base_weight_var = tk.StringVar(value=str(self.config.get("base_weight", 5555)))
        self.base_weight_entry = ttk.Entry(self.weight_frame, textvariable=self.base_weight_var, width=12)
        self.base_weight_entry.pack(side=tk.LEFT, padx=5)
        self.weight_frame.pack(anchor="w")
        
        # Command mode: Controls
        self.cmd_frame = ttk.Frame(self.mode_frame)
        
        # Command selector
        cmd_row1 = ttk.Frame(self.cmd_frame)
        cmd_row1.pack(fill=tk.X, pady=2)
        ttk.Label(cmd_row1, text="Command:").pack(side=tk.LEFT)
        self.command_var = tk.StringVar(value=self.config.get("selected_command", "IP"))
        self.command_combo = ttk.Combobox(cmd_row1, textvariable=self.command_var, values=list(COMMAND_DEFINITIONS.keys()), width=12)
        self.command_combo.pack(side=tk.LEFT, padx=5)
        
        # Command description label
        self.command_desc_var = tk.StringVar(value=COMMAND_DEFINITIONS["IP"])
        self.command_desc_label = ttk.Label(self.cmd_frame, textvariable=self.command_desc_var, foreground="#555555", font=("Arial", 8), wraplength=250)
        self.command_desc_label.pack(fill=tk.X, pady=(2, 8))
        self.command_combo.bind("<<ComboboxSelected>>", self._on_command_select)
        
        # Custom command input
        cmd_row2 = ttk.Frame(self.cmd_frame)
        cmd_row2.pack(fill=tk.X, pady=2)
        ttk.Label(cmd_row2, text="Custom:").pack(side=tk.LEFT)
        self.custom_command_var = tk.StringVar(value=self.config.get("custom_command", ""))
        self.custom_command_entry = ttk.Entry(cmd_row2, textvariable=self.custom_command_var, width=15)
        self.custom_command_entry.pack(side=tk.LEFT, padx=5)
        
        # Recent commands dropdown
        cmd_row3 = ttk.Frame(self.cmd_frame)
        cmd_row3.pack(fill=tk.X, pady=2)
        ttk.Label(cmd_row3, text="Recent:").pack(side=tk.LEFT)
        self.recent_command_var = tk.StringVar()
        self.recent_command_combo = ttk.Combobox(cmd_row3, textvariable=self.recent_command_var, width=12)
        self.recent_command_combo.pack(side=tk.LEFT, padx=5)
        
        # Delay and options
        cmd_row4 = ttk.Frame(self.cmd_frame)
        cmd_row4.pack(fill=tk.X, pady=2)
        ttk.Label(cmd_row4, text="Delay (ms):").pack(side=tk.LEFT)
        self.delay_var = tk.StringVar(value=str(self.config.get("delay_time", 1000)))
        self.delay_combo = ttk.Combobox(cmd_row4, textvariable=self.delay_var, values=[100, 200, 500, 1000, 2000, 3000, 5000], width=8)
        self.delay_combo.pack(side=tk.LEFT, padx=5)
        
        # Keep open checkbox
        self.keep_open_var = tk.BooleanVar(value=False)
        self.keep_open_check = ttk.Checkbutton(self.cmd_frame, text="Keep Port Open", variable=self.keep_open_var)
        self.keep_open_check.pack(anchor="w", pady=2)
        
        # Auto-reconnect checkbox
        self.auto_reconnect_var = tk.BooleanVar(value=self.config.get("auto_reconnect", False))
        self.auto_reconnect_check = ttk.Checkbutton(self.cmd_frame, text="Auto-Reconnect", variable=self.auto_reconnect_var)
        self.auto_reconnect_check.pack(anchor="w", pady=2)
        
        # Configure grid weights
        settings_frame.columnconfigure(1, weight=1)
    
    def _setup_control_frame(self, parent):
        """Set up the control buttons frame."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.pack(fill=tk.BOTH, expand=True)
        
        # First row: Connect + Disconnect
        connect_row = ttk.Frame(control_frame)
        connect_row.pack(fill=tk.X, pady=2)
        
        self.connect_btn = tk.Button(
            connect_row,
            text="🔗 Connect",
            command=self._connect,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        )
        self.connect_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.disconnect_btn = tk.Button(
            connect_row,
            text="✂ Disconnect",
            command=self._disconnect,
            bg="#9E9E9E",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        )
        self.disconnect_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        # Separator
        ttk.Separator(control_frame, orient='horizontal').pack(fill=tk.X, pady=8)
        
        # Second row: Start + Stop
        action_row = ttk.Frame(control_frame)
        action_row.pack(fill=tk.X, pady=2)
        
        self.start_btn = tk.Button(
            action_row,
            text="▶ Start",
            command=self._start,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.stop_btn = tk.Button(
            action_row,
            text="■ Stop",
            command=self._stop,
            bg="#f44336",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
    
    def _setup_status_frame(self, parent):
        """Set up the status frame."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Connection indicator
        self.indicator_canvas = tk.Canvas(status_frame, width=16, height=16, highlightthickness=0)
        self.indicator_canvas.pack(side=tk.LEFT, padx=(0, 5))
        self._indicator = self.indicator_canvas.create_oval(2, 2, 14, 14, fill="#808080", outline="#606060")
        
        # Status label
        self.status_var = tk.StringVar(value="Status: Not Connected")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        # Mode info label
        self.mode_info_var = tk.StringVar()
        self.mode_info_label = ttk.Label(status_frame, textvariable=self.mode_info_var, foreground="#666666")
        self.mode_info_label.pack(side=tk.RIGHT)
    
    def _setup_log_frame(self, parent):
        """Set up the log display frame."""
        log_frame = ttk.LabelFrame(parent, text="Communication Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame for log controls
        btn_frame = ttk.Frame(log_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Clear log button
        clear_btn = ttk.Button(btn_frame, text="Clear Log", command=self._clear_log, width=10)
        clear_btn.pack(side=tk.RIGHT)
        
        # Save log button
        save_btn = ttk.Button(btn_frame, text="Save Log", command=self._save_log, width=10)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Timestamp checkbox
        self.show_timestamps_var = tk.BooleanVar(value=self.config.get("show_timestamps", True))
        timestamp_check = ttk.Checkbutton(btn_frame, text="Show Timestamps", variable=self.show_timestamps_var)
        timestamp_check.pack(side=tk.LEFT)
        
        # Log text with scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
            selectbackground="#264f78",
            height=15,
            state=tk.DISABLED
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text tags for colored output
        self.log_text.tag_configure("INFO", foreground="#4ec9b0")
        self.log_text.tag_configure("ERROR", foreground="#f44747")
        self.log_text.tag_configure("WARNING", foreground="#dcdcaa")
        self.log_text.tag_configure("SUCCESS", foreground="#4fc3f7")
        self.log_text.tag_configure("SENT", foreground="#ce9178")
        self.log_text.tag_configure("RECEIVED", foreground="#b5cea8")
    
    def _setup_tooltips(self):
        """Set up tooltips for widgets."""
        tooltips = {
            self.com_combo: "Select the COM port to connect to",
            self.baud_combo: "Communication speed (bits per second)",
            self.parity_combo: "Error detection method",
            self.data_bits_combo: "Number of data bits per frame",
            self.stop_bits_combo: "Number of stop bits",
            self.mode_combo: "Operating mode:\n• Transmit: Send weight data\n• Receive: Read incoming data\n• Command: Send commands",
            self.base_weight_entry: "Base weight value to transmit (0-999999)",
            self.command_combo: "Select a predefined command",
            self.custom_command_entry: "Enter a custom command string",
            self.delay_combo: "Delay before closing port after command",
            self.start_btn: "Start transmission/reception (F5)",
            self.stop_btn: "Stop transmission/reception (Escape)",
            self.connect_btn: "Connect to selected port (Ctrl+O)",
            self.disconnect_btn: "Disconnect from port (Ctrl+D)"
        }
        
        for widget, text in tooltips.items():
            ToolTip(widget, text)
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        self.root.bind("<F5>", lambda e: self._start())
        self.root.bind("<Escape>", lambda e: self._stop())
        self.root.bind("<Control-o>", lambda e: self._connect())
        self.root.bind("<Control-d>", lambda e: self._disconnect())
        self.root.bind("<Control-l>", lambda e: self._clear_log())
        self.root.bind("<Control-r>", lambda e: self._refresh_com_ports())
    
    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================
    
    def _on_mode_change(self, *args):
        """Handle mode change."""
        mode = self.mode_var.get()
        
        # Hide all mode-specific frames
        self.weight_frame.pack_forget()
        self.cmd_frame.pack_forget()
        
        # Show appropriate frame
        if mode == "transmit":
            self.weight_frame.pack(anchor="w")
            self.mode_info_var.set("Mode: Transmit weight data")
        elif mode == "receive":
            self.mode_info_var.set("Mode: Receive incoming data")
        elif mode == "command":
            self.cmd_frame.pack(anchor="w", fill=tk.X)
            self._update_recent_commands()
            self.mode_info_var.set("Mode: Send commands")
        
        self._update_settings()
    
    def _on_recent_command_select(self, *args):
        """Handle recent command selection."""
        selected = self.recent_command_var.get()
        if selected:
            self.custom_command_var.set(selected)
            self.recent_command_var.set("")
    
    def _on_baudrate_change(self, *args):
        """Handle baudrate change with non-blocking implementation."""
        try:
            new_baudrate = int(self.baud_var.get())
            old_baudrate = self.config.get("baud_rate", 9600)
            
            # Update configuration immediately
            self.config["baud_rate"] = new_baudrate
            self._save_config()
            
            # If not connected, just update settings
            if not self.connection.is_connected:
                self._log_message(f"Baudrate changed to {new_baudrate} (will apply on next connection)", "INFO")
                return
            
            # If connected and different baudrate, schedule reconnection
            if new_baudrate != old_baudrate:
                self._log_message(f"Will change baudrate from {old_baudrate} to {new_baudrate}...", "INFO")
                
                # Schedule the baudrate change in the main thread to avoid conflicts
                self.root.after(100, lambda: self._apply_baudrate_change(new_baudrate, old_baudrate))
            else:
                self._log_message(f"Baudrate already set to {new_baudrate}", "INFO")
                
        except ValueError:
            self._log_message("Invalid baudrate value", "ERROR")
            # Revert to previous valid value
            self.baud_var.set(str(self.config.get("baud_rate", 9600)))
        except Exception as e:
            self._log_message(f"Error changing baudrate: {e}", "ERROR")
    
    def _apply_baudrate_change(self, new_baudrate: int, old_baudrate: int):
        """Apply baudrate change safely in main thread."""
        try:
            # Stop operations if running
            was_running = self._running
            if was_running:
                self._stop()
                time.sleep(0.1)  # Brief pause
            
            # Disconnect
            success, message = self.connection.disconnect()
            if success:
                self._log_message(f"Disconnected: {message}", "INFO")
            
            # Reconnect with new baudrate
            serial_config = self._get_serial_config()
            success, message = self.connection.connect(serial_config)
            
            if success:
                self._log_message(f"Reconnected at {new_baudrate} baud: {message}", "SUCCESS")
                self._update_connection_indicator()
                
                # Resume operations if they were running
                if was_running:
                    self._start()
            else:
                self._log_message(f"Failed to reconnect at {new_baudrate}: {message}", "ERROR")
                # Revert to old baudrate
                self.baud_var.set(str(old_baudrate))
                self.config["baud_rate"] = old_baudrate
                self._save_config()
                
        except Exception as e:
            self._log_message(f"Error applying baudrate change: {e}", "ERROR")
    
    def _on_command_select(self, *args):
        """Update command description when command is selected."""
        selected_cmd = self.command_var.get()
        self.command_desc_var.set(COMMAND_DEFINITIONS.get(selected_cmd, ""))
        self._update_settings()
    
    def _update_recent_commands(self):
        """Update recent commands dropdown."""
        self.recent_command_combo['values'] = self.recent_commands
    
    def _add_to_recent_commands(self, command: str):
        """Add command to recent commands list."""
        if command and command not in self.recent_commands:
            self.recent_commands.insert(0, command)
            self.recent_commands = self.recent_commands[:self.config.get("max_recent_commands", 10)]
            self._update_recent_commands()
    
    # ========================================================================
    # SERIAL OPERATIONS
    # ========================================================================
    
    def _get_com_ports(self) -> List[str]:
        """Get list of available COM ports."""
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return sorted(ports) if ports else []
        except Exception:
            return []
    
    def _refresh_com_ports(self):
        """Refresh COM port list."""
        ports = self._get_com_ports()
        self.com_combo['values'] = ports
        if ports:
            self.com_var.set(ports[0])
            self._log_message(f"Found {len(ports)} COM port(s): {', '.join(ports)}", "INFO")
        else:
            self._log_message("No COM ports found", "WARNING")
    
    def _update_settings(self):
        """Update settings from UI."""
        try:
            self.config["com_port"] = self.com_var.get()
            self.config["baud_rate"] = int(self.baud_var.get())
            self.config["parity"] = self.parity_var.get()
            self.config["data_bits"] = int(self.data_bits_var.get())
            self.config["stop_bits"] = self.stop_bits_var.get()
            self.config["mode"] = self.mode_var.get()
            self.config["auto_reconnect"] = self.auto_reconnect_var.get()
            
            if self.config["mode"] == "transmit":
                weight = int(self.base_weight_var.get())
                if not 0 <= weight <= 999999:
                    raise ValueError("Base weight must be between 0 and 999999")
                self.config["base_weight"] = weight
            elif self.config["mode"] == "command":
                self.config["selected_command"] = self.command_var.get()
                self.config["custom_command"] = self.custom_command_var.get()
                self.config["delay_time"] = int(self.delay_var.get())
                self.config["recent_commands"] = self.recent_commands
            
        except ValueError as e:
            self._log_message(f"Invalid input: {e}", "ERROR")
    
    def _get_serial_config(self) -> SerialConfig:
        """Get current serial configuration."""
        return SerialConfig(
            com_port=self.config["com_port"],
            baud_rate=self.config["baud_rate"],
            parity=self.config["parity"],
            data_bits=self.config["data_bits"],
            stop_bits=self.config["stop_bits"]
        )
    
    def _connect(self):
        """Connect to serial port."""
        # Save current user selection before refresh
        current_selected_port = self.com_var.get()
        
        # Refresh port list
        self._refresh_com_ports()
        
        # Restore user's selected port if it still exists
        available_ports = self._get_com_ports()
        if current_selected_port in available_ports:
            self.com_var.set(current_selected_port)
        
        # Update config with final selection
        self.config["com_port"] = self.com_var.get()
        
        # Check after refresh
        if not self.config["com_port"]:
            messagebox.showwarning("No Port Selected", "No COM ports detected on this system.")
            return
        
        config = self._get_serial_config()
        success, message = self.connection.connect(config)
        
        if success:
            self._log_message(message, "SUCCESS")
            self._update_connection_indicator()
        else:
            self._log_message(message, "ERROR")
            messagebox.showerror("Connection Failed", message)
    
    def _disconnect(self):
        """Disconnect from serial port."""
        if self._running:
            self._stop()
        
        success, message = self.connection.disconnect()
        self._log_message(message, "INFO" if success else "WARNING")
        self._update_connection_indicator()
    
    def _start(self):
        """Start transmission/reception."""
        if self._running:
            return
        
        # Connect if not already connected
        if not self.connection.is_connected:
            if not self.config["com_port"]:
                messagebox.showwarning("No Port Selected", "Please select a COM port first.")
                return
            
            config = self._get_serial_config()
            success, message = self.connection.connect(config)
            if not success:
                self._log_message(message, "ERROR")
                messagebox.showerror("Connection Failed", message)
                return
            self._log_message(message, "SUCCESS")
            self._update_connection_indicator()
        
        self._stop_event.clear()
        self._running = True
        
        # Start appropriate thread based on mode
        mode = self.config.get("mode", "transmit")
        if mode == "transmit":
            self._thread = threading.Thread(target=self._transmit_loop, daemon=True)
            self._thread.start()
            self._log_message("Transmission started", "INFO")
        elif mode == "receive":
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            self._log_message("Reception started", "INFO")
        elif mode == "command":
            self._send_command()
        
        self._update_button_states()
        
    def _stop(self):
        """Stop transmission/reception."""
        if not self._running:
            return
        
        # Set stop flag and update state immediately
        self._stop_event.set()
        self._running = False
        
        # Update UI immediately
        self._update_button_states()
        self._log_message("Stopped", "INFO")
        
        # Don't wait for threads - let them finish naturally
        # This prevents freezing when threads are stuck
    
    def _transmit_loop(self):
        """Transmit loop for sending weight data."""
        while not self._stop_event.is_set() and self._running:
            try:
                # Always read live value directly from UI entry box
                base_weight_input = self.base_weight_var.get().strip()
                if base_weight_input.isdigit():
                    base_weight = int(base_weight_input)
                else:
                    # Fallback to stored config value if invalid
                    base_weight = self.config["base_weight"]
                weight_str = f"{base_weight:06d}"
                reversed_digits = weight_str[::-1]
                payload_str = f"={reversed_digits}"
                payload_bytes = payload_str.encode('ascii')
                
                written, error = self.connection.write(payload_bytes)
                
                if error:
                    self._log_message(f"Write error: {error}", "ERROR")
                    if self.config.get("auto_reconnect"):
                        self._schedule_reconnect()
                    break
                elif written == 0:
                    self._log_message("No bytes written", "WARNING")
                else:
                    self._log_message(f"Sent: '{payload_str}' ({written} bytes)", "SENT")
                
                time.sleep(0.2)
                
            except Exception as e:
                self._log_message(f"Transmit error: {e}", "ERROR")
                break
        
        self._queue_message(lambda: self._update_button_states())
    
    def _receive_loop(self):
        """Simple receive loop - just show raw scale data."""
        data_buffer = ""
        last_logged_data = ""
        
        while not self._stop_event.is_set() and self._running:
            try:
                data, error = self.connection.read_line()
                
                if error:
                    break
                elif data:
                    try:
                        # Add new data to buffer
                        decoded = data.decode('ascii', errors='ignore')
                        data_buffer += decoded
                        
                        # Process complete lines
                        while '\n' in data_buffer or '\r' in data_buffer:
                            # Find the next line ending
                            line_end = min(
                                data_buffer.find('\n') if '\n' in data_buffer else len(data_buffer),
                                data_buffer.find('\r') if '\r' in data_buffer else len(data_buffer)
                            )
                            
                            if line_end < len(data_buffer):
                                # Extract the complete line
                                line = data_buffer[:line_end].strip()
                                data_buffer = data_buffer[line_end + 1:]
                                
                                # Remove any remaining \r if \n was found
                                if data_buffer.startswith('\r'):
                                    data_buffer = data_buffer[1:]
                                
                                # Only log if we have meaningful data and it's not a duplicate
                                if line and line != last_logged_data:
                                    self._log_message(line, "RECEIVED")
                                    last_logged_data = line
                            else:
                                break
                        
                        # If buffer gets too large without line endings, process it
                        if len(data_buffer) > 100:
                            if data_buffer.strip() and data_buffer.strip() != last_logged_data:
                                self._log_message(data_buffer.strip(), "RECEIVED")
                                last_logged_data = data_buffer.strip()
                            data_buffer = ""
                            
                    except Exception:
                        # Log raw data if decode fails
                        if data and data.hex() != last_logged_data:
                            self._log_message(data.hex(), "RECEIVED")
                            last_logged_data = data.hex()
                        data_buffer = ""  # Clear buffer on error
                
                time.sleep(0.02)
                
            except Exception:
                break
        
        # Process any remaining data in buffer when stopping
        if data_buffer.strip() and data_buffer.strip() != last_logged_data:
            self._log_message(data_buffer.strip(), "RECEIVED")
        
        self._queue_message(lambda: self._update_button_states())
    
    def _send_command(self):
        """Send a single command."""
        try:
            # Get command - custom command overrides selected command
            custom_cmd = self.custom_command_var.get().strip()
            if custom_cmd:
                cmd = custom_cmd
            else:
                cmd = self.command_var.get()
            
            # Add to recent commands
            self._add_to_recent_commands(cmd)
            
            # Prepare payload
            payload_bytes = bytes(ord(c) for c in cmd.upper()) + b'\r\n'
            
            written, error = self.connection.write(payload_bytes)
            
            if error:
                self._log_message(f"Command failed: {error}", "ERROR")
            else:
                self._log_message(f"Sent command: '{cmd}' → {list(payload_bytes)} ({written} bytes)", "SENT")
            
            # Handle post-command behavior
            if self.keep_open_var.get():
                self._log_message("Port kept open", "INFO")
            else:
                delay = self.config["delay_time"]
                self.root.after(delay, self._close_after_command)
            
        except Exception as e:
            self._log_message(f"Command error: {e}", "ERROR")
        
        self._running = False
        self._update_button_states()
    
    def _close_after_command(self):
        """Close connection after command with delay."""
        if not self.keep_open_var.get():
            self.connection.disconnect()
            self._update_connection_indicator()
            self._log_message("Command completed, port closed", "INFO")
    
    def _schedule_reconnect(self):
        """Schedule automatic reconnection attempt."""
        interval = self.config.get("reconnect_interval", 5000)
        self._log_message(f"Scheduling reconnect in {interval}ms...", "WARNING")
        self.root.after(interval, self._attempt_reconnect)
    
    def _attempt_reconnect(self):
        """Attempt to reconnect."""
        if self._running and not self.connection.is_connected:
            config = self._get_serial_config()
            success, message = self.connection.connect(config)
            if success:
                self._log_message("Auto-reconnected successfully", "SUCCESS")
                self._update_connection_indicator()
            else:
                self._log_message(f"Auto-reconnect failed: {message}", "ERROR")
                self._schedule_reconnect()
    
    # ========================================================================
    # UI UPDATES
    # ========================================================================
    
    def _update_button_states(self):
        """Update button states based on running status."""
        if self._running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
    
    def _update_connection_indicator(self):
        """Update connection status indicator."""
        if self.connection.is_connected:
            self.indicator_canvas.itemconfig(self._indicator, fill="#4CAF50", outline="#388E3C")
            self.status_var.set(f"Status: Connected to {self.config['com_port']}")
        else:
            self.indicator_canvas.itemconfig(self._indicator, fill="#808080", outline="#606060")
            self.status_var.set("Status: Not Connected")
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    def _queue_message(self, callback):
        """Queue a message for the main thread."""
        self._message_queue.put(callback)
    
    def _process_message_queue(self):
        """Process queued messages."""
        try:
            while True:
                callback = self._message_queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._process_message_queue)
    
    def _log_message(self, message: str, level: str = "INFO"):
        """Log message to GUI and file."""
        def _update():
            timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S") if self.show_timestamps_var.get() else ""
            prefix = f"[{timestamp}] " if timestamp else ""
            full_msg = f"{prefix}{level}: {message}\n"
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, full_msg, level)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            
            # Also log to file
            log_level = getattr(logging, level, logging.INFO)
            logging.log(log_level, message)
        
        # Ensure thread-safe update
        if threading.current_thread() != threading.main_thread():
            self.root.after(0, _update)
        else:
            _update()
    
    def _clear_log(self):
        """Clear the log display."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log_message("Log cleared", "INFO")
    
    def _save_log(self):
        """Save log to file."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfilename=f"serial_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._log_message(f"Log saved to {filename}", "SUCCESS")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save log: {e}")
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def _on_closing(self):
        """Handle window close event."""
        # Stop any running operations
        self._stop()
        
        # Disconnect
        self.connection.disconnect()
        
        # Save configuration
        self.config["window_geometry"] = self.root.geometry()
        self.config["recent_commands"] = self.recent_commands
        self._save_config()
        
        # Destroy window
        self.root.destroy()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    setup_logging()
    
    root = tk.Tk()
    app = SerialTransmitterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()