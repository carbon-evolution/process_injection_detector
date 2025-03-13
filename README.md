# Process Injection Detector

A Windows-based security tool that monitors running processes and detects malicious code injection techniques commonly used by malware, exploits, and advanced persistent threats (APTs).

## Overview

Process injection is a technique used by malware to insert and execute malicious code within the address space of legitimate processes. This allows attackers to evade detection, bypass security controls, and gain persistence. This tool continuously monitors running processes for signs of various injection techniques, providing real-time alerts when suspicious activity is detected.

## Injection Techniques Detected

This tool can detect several common process injection techniques:

1. **Classic DLL Injection** - Detection of suspicious DLLs loaded from unusual locations (temp folders, downloads)
2. **Process Hollowing** - Identification of processes with modified PE headers and suspicious thread start addresses
3. **Memory Permission Anomalies** - Detection of memory regions with suspicious RWX (read-write-execute) permissions

## Project Structure

This project is structured as a Python package for better organization and maintainability:

```
process_injection_detector/
├── process_injection_detector/       # Main package
│   ├── __init__.py                   # Package initialization
│   └── detector.py                   # Core implementation
├── tests/                            # Unit tests
│   ├── __init__.py                   # Test package initialization
│   └── test_basic.py                 # Basic unit tests
├── config.json                       # Configuration file
├── setup.py                          # Package installation script
├── requirements.txt                  # Python dependencies
├── run_detector.py                   # Script to run the detector
├── test_injection.c                  # Test DLL source for injection testing
├── README.md                         # This documentation
├── LICENSE                           # MIT License
├── CONTRIBUTING.md                   # Guidelines for contributors
└── .gitignore                        # Git ignore patterns
```

## Requirements

- Windows 10/11
- Python 3.7+
- Administrator privileges (required for deep process inspection)
- Required Python packages (specified in requirements.txt):
  - psutil >= 5.9.0
  - pywin32 >= 302
  - dataclasses (for Python < 3.7)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/process-injection-detector.git
cd process-injection-detector
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. (Optional) Install as a package:
```
pip install -e .
```

## Usage

### Running the Detector

Run the tool with administrator privileges:

```
# Right-click on PowerShell/Command Prompt and select "Run as administrator"
python run_detector.py
```

Alternatively, if installed as a package:
```
process-injection-detector
```

### What to Expect When Running

When running this script:

1. You will see a single `python.exe` process in Windows Task Manager
2. The process will run with elevated privileges
3. The tool continuously scans all running processes (except whitelisted ones)
4. It logs activities to both console and log file
5. If suspicious activities are detected, detailed alerts are generated

### Configuration

The tool creates or uses a `config.json` file with default settings:

```json
{
    "whitelisted_processes": ["explorer.exe", "svchost.exe"],
    "scan_interval": 2,
    "alert_email": "",
    "log_level": "INFO"
}
```

- **whitelisted_processes**: List of process names to ignore during scanning
- **scan_interval**: Time between scans (in seconds)
- **alert_email**: Email address for alerts (if alert mechanism is implemented)
- **log_level**: Logging level (DEBUG, INFO, WARNING, ERROR)

## Testing with the Included Test DLL

This project includes a harmless test DLL source file (`test_injection.c`) that you can use to safely test the process injection detection capabilities.

### Compiling the Test DLL

1. **Using Visual Studio Command Prompt**:
   ```
   cl.exe /LD test_injection.c user32.lib
   ```

2. **Using MinGW**:
   ```
   gcc -shared -o test_injection.dll test_injection.c -luser32
   ```

### Using the Test DLL

1. First, start the Process Injection Detector:
   ```
   python run_detector.py
   ```

2. Then use a DLL injection tool to inject the compiled DLL into a target process. Some options include:

   - **Process Hacker**: Open Process Hacker, right-click on a process (like notepad.exe), select "Miscellaneous" → "Inject DLL", and navigate to your test_injection.dll
   
   - **Simple injector script**: You can use this simple Python script (save as `inject_test.py`):
   
   ```python
   import ctypes
   import sys
   from ctypes import windll
   import time
   
   # Make sure to run this script as administrator
   
   if len(sys.argv) != 3:
       print("Usage: inject_test.py <PID> <path_to_dll>")
       sys.exit(1)
       
   pid = int(sys.argv[1])
   dll_path = sys.argv[2]
   
   # Get process handle
   h_process = windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
   
   if h_process == 0:
       print(f"Failed to open process {pid}")
       sys.exit(1)
       
   # Allocate memory for DLL path
   path_len = len(dll_path) + 1
   remote_memory = windll.kernel32.VirtualAllocEx(h_process, 0, path_len, 0x1000, 0x40)
   
   # Write DLL path to process memory
   written = ctypes.c_int(0)
   windll.kernel32.WriteProcessMemory(h_process, remote_memory, dll_path, path_len, ctypes.byref(written))
   
   # Get address of LoadLibraryA
   h_kernel32 = windll.kernel32.GetModuleHandleA(b"kernel32.dll")
   h_loadlib = windll.kernel32.GetProcAddress(h_kernel32, b"LoadLibraryA")
   
   # Create remote thread that calls LoadLibraryA(dll_path)
   thread_id = ctypes.c_int(0)
   windll.kernel32.CreateRemoteThread(h_process, 0, 0, h_loadlib, remote_memory, 0, ctypes.byref(thread_id))
   
   print(f"Injected {dll_path} into process {pid}")
   
   # Give some time for injection to complete
   time.sleep(1)
   
   # Clean up
   windll.kernel32.CloseHandle(h_process)
   ```
   
   Run it with:
   ```
   python inject_test.py <target_process_id> <path_to_test_injection.dll>
   ```

3. **Expected Results**:
   - A message box will appear, confirming successful injection
   - The Process Injection Detector should log this as a suspicious activity
   - Check the `detection_events.json` file for the recorded event

### Safe Testing Practices

- Always test in a controlled environment
- Target only processes you own (like notepad.exe or calc.exe)
- Consider using a virtual machine for testing

## Output and Reporting

The tool generates several outputs:

1. **Console Output**: Real-time monitoring information and alerts
2. **Log File**: All activities are logged to `process_injection_detector.log`
3. **Detection Events**: Suspicious activities are saved to `detection_events.json` as structured data

Example alert:
```
⚠️ Potential Process Injection Detected!
Process: suspicious_process.exe (PID: 1234)
Details: {'activities': ['Suspicious DLL location: C:\\temp\\malicious.dll']}
```

## Technical Details

### How It Works

1. **Process Enumeration**: Uses psutil to enumerate all running processes
2. **Process Analysis**:
   - Gathers detailed process information (PID, path, command line, etc.)
   - Verifies digital signatures of executable files
   - Calculates file hashes for identification
3. **Memory Analysis**:
   - Examines memory maps and permissions
   - Checks for DLLs loaded from suspicious locations
   - Analyzes memory regions with executable permissions
4. **Hollowing Detection**:
   - Checks for modified PE headers
   - Analyzes thread start addresses
5. **Event Handling**:
   - Logs suspicious activities
   - Saves structured data for further analysis
   - Provides alerts via console and logs

### Resource Utilization

The detector uses minimal system resources:
- CPU usage varies based on the number of processes (typically 1-5%)
- Memory usage is generally under 50MB
- Disk activity occurs only when writing logs or detection events

## Limitations

- Requires administrator privileges
- May generate false positives with certain legitimate applications
- Only detects injections that occur while the tool is running
- Some evasive malware may still avoid detection
- Advanced injection techniques may require additional detection methods

## Contributing

If you'd like to contribute to this project, please see the CONTRIBUTING.md file for guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and defensive security purposes only. It's designed to help identify potentially malicious activities but should be used responsibly and legally. Always ensure you have proper authorization before monitoring systems. 