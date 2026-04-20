# Serial Port Tester

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-orange.svg)](https://github.com)

A comprehensive serial communication testing tool with an intuitive GUI for testing, debugging, and monitoring serial port communications. Perfect for working with weighing scales, industrial equipment, and other serial devices.

![Serial Port Tester Screenshot](assets/screenshot.png)

## ✨ Features

### Operating Modes

- **Transmit Mode**: Send continuous weight data to external displays
- **Receive Mode**: Monitor and log incoming serial data
- **Command Mode**: Send predefined or custom commands to serial devices

### Key Capabilities

- 🔌 **Easy Connection Management**: Quick COM port selection with auto-refresh
- 📊 **Real-time Logging**: Color-coded communication log with timestamps
- ⚙️ **Flexible Configuration**: Full serial parameter customization
- 💾 **Persistent Settings**: Automatic configuration saving/loading
- 🔄 **Auto-Reconnect**: Automatic reconnection on connection loss
- 📝 **Command History**: Quick access to recently used commands
- ⌨️ **Keyboard Shortcuts**: Efficient workflow with hotkeys
- 🎨 **Modern Dark Theme**: Easy on the eyes for extended use

## 📋 Requirements

### To run EXE (no installation needed):
- Windows 10 / Windows 11
- **No Python required**

### To run from source:
- Python 3.8 or higher
- Windows, Linux, or macOS

## 🚀 Installation

### Option 1: Run from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/serial-port-tester.git
   cd serial-port-tester
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install pyserial
   ```

4. Run the application:
   ```bash
   python serial_transmitter.py
   ```

### Option 2: Build Executable (Windows)

A pre-configured build script is included for one-click compilation:

```batch
build_portable.cmd
```

This will automatically:
✅ Install required dependencies
✅ Build completely standalone single EXE file
✅ Include application icon properly
✅ Create portable version that runs without installation

Or manual build:
```bash
pip install pyserial pyinstaller
pyinstaller --onefile --windowed --icon="RS232.ico" --name="Serial Port Tester" --hidden-import=tkinter serial_transmitter.py
```

3. The executable will be in the `dist` folder.

## 📖 Usage Guide

### Serial Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| COM Port | Serial port to connect to | Auto-detect |
| Baud Rate | Communication speed (bits/sec) | 9600 |
| Parity | Error detection method | None |
| Data Bits | Bits per data frame | 8 |
| Stop Bits | Stop bits at frame end | One |

### Operating Modes

#### Transmit Mode
Sends weight data continuously to connected devices (e.g., big displays).

- Enter a base weight value (0-999999)
- Data is formatted and transmitted at regular intervals
- Weight digits are reversed as per protocol requirements

#### Receive Mode
Monitors incoming serial data and displays it in the log.

- Connect to scales with COM assignment set to Demand or Continuous Output
- All received data is logged with timestamps
- Supports ASCII data decoding

#### Command Mode
Send commands to serial devices (e.g., weighing indicators).

- Select from predefined commands or enter custom ones
- Configurable delay before closing port
- Option to keep port open for multiple commands

### Available SICS Commands

| Command | Description |
|---------|-------------|
| `@` | Reset the scale |
| `I0` | Inquiry of all available SICS commands |
| `I1` | Inquiry of SICS level and SICS versions |
| `I2` | Inquiry of scale data |
| `I3` | Inquiry of scale software version |
| `I4` | Inquiry of serial number |
| `I10` | Inquire or set scale ID |
| `I11` | Inquire of scale type |
| `S` | Send stable weight value |
| `SI` | Send weight value immediately |
| `SIR` | Send weight value repeatedly |
| `Z` | Zero the scale |
| `ZI` | Zero immediately |
| `D` | Write text into display |
| `DW` | Weight display |
| `SR` | Send and repeat stable weight value |
| `T` | Tare |
| `TA` | Tare value |
| `TAC` | Clear tare |
| `TI` | Tare immediately |
| `C2` | Calibrate with the external calibration weight |
| `C3` | Calibrate with the internal calibration weight |
| `P100` | Print out on the printer |
| `P101` | Print out stable weight value |
| `P102` | Print out current weight value immediately |
| `SIRU` | Send weight value in the current unit immediately and repeat |
| `SIU` | Send weight value in the current unit immediately |
| `SNR` | Send stable weight value and repeat after every weight change |
| `SNRU` | Send stable weight value in the current unit and repeat after every weight change |
| `SRU` | Send weight value in the current unit and repeat |
| `ST` | After pressing the Transfer key, send the stable weight value |
| `SU` | Send stable weight value in the current unit |
| `LST` | Send menu settings |
| `M01` | Weighing mode |
| `M02` | Stability setting |
| `M03` | Autozero function |
| `M19` | Send calibration weight |
| `M21` | Inquire/set weight unit |
| `P` | Print text |
| `PRN` | Print out at every printer interface |
| `RST` | Restart |
| `SFIR` | Send weight value immediately and repeat quickly |
| `SIH` | Send weight value immediately in high resolution |
| `SWU` | Switch weight unit |
| `SX` | Send stable data record |
| `SXI` | Send data record immediately |
| `SXIR` | Send data record immediately and repeat |
| `U` | Switch weight unit |
| `IP` | Initialize/Identification - Query device identity |
| `CP` | Clear Print - Clear print buffer |
| `SP` | Set Parameters - Configure device parameters |
| `xS` | Set Unit/Scale - Configure measurement unit |
| `xP` | Set Precision - Set decimal precision |
| `xT` | Set Tare - Configure tare value |
| `PU` | Print Unit - Print current unit |
| `xU` | Set Unit - Set measurement unit |
| `xM` | Set Mode - Change device mode |
| `PV` | Print Value - Print current value |
| `Esc R` | Escape Response - Reset/Response command |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F5 | Start transmission/reception |
| Escape | Stop transmission/reception |
| Ctrl+O | Connect to port |
| Ctrl+D | Disconnect from port |
| Ctrl+L | Clear log |
| Ctrl+R | Refresh COM ports |

## 📁 Project Structure

```
serial-port-tester/
├── serial_transmitter.py    # Main application code
├── build_portable.cmd       # One-click Windows portable build script
├── RS232.ico                # Application icon
├── assets/
│   └── screenshot.png      # Application screenshot
├── serial_transmission.log # Auto-generated runtime log
├── serial_tester_config.json # Auto-generated saved preferences
├── README.md               # This file
└── LICENSE                 # MIT License
```

## 🔧 Configuration

The application automatically saves your settings to `serial_tester_config.json`:

```json
{
  "com_port": "COM4",
  "baud_rate": 9600,
  "parity": "None",
  "data_bits": 8,
  "stop_bits": "One",
  "mode": "transmit",
  "base_weight": 5555,
  "recent_commands": ["IP", "P", "T"],
  "window_geometry": "600x700"
}
```

## ⬇️ Download Prebuilt Version

You can download the ready-to-use compiled EXE from the [Releases Page](https://github.com/yourusername/serial-port-tester/releases).

Just download, extract, and run - no installation required.

---

## 🐛 Troubleshooting

### Port Not Found
- Ensure the device is connected and powered on
- Check Device Manager (Windows) or `ls /dev/tty*` (Linux)
- Try refreshing the port list with the 🔄 button or Ctrl+R

### Access Denied
- Another application may be using the port
- Close any other serial terminal applications
- Try disconnecting and reconnecting the device

### No Data Received
- Verify baud rate matches the device settings
- Check cable connections (TX/RX may need to be swapped)
- Ensure the device is configured to send data

### Connection Drops
- Enable "Auto-Reconnect" in command mode
- Check for cable issues or loose connections
- Review the log file for error details

## 📥 Installation

### Quick Start (Windows):
1. Download latest EXE from Releases
2. Save to any folder
3. Double-click to run

> ✅ **This is a portable application**. It will not write to system directories or modify your system. All settings are saved in the same folder.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Python](https://www.python.org/) and [Tkinter](https://docs.python.org/3/library/tkinter.html)
- Serial communication powered by [pyserial](https://pythonhosted.org/pyserial/)
- Icon from [RS232](https://en.wikipedia.org/wiki/RS-232) standard

## 📧 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/serial-port-tester/issues) on GitHub.

---

**Made with ❤️ for the embedded systems community**