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
├── test_injection.dll                # Compiled test DLL for injection testing
├── inject_test.py                    # DLL injection test script
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

This project includes a harmless test DLL source file (`test_injection.c`) and an injection script that you can use to safely test the process injection detection capabilities.

### Compiling the Test DLL

Before using the test scripts, compile the test DLL:

1. **Using Visual Studio Command Prompt**:
   ```
   cl.exe /LD test_injection.c user32.lib
   ```

2. **Using MinGW**:
   ```
   gcc -shared -o test_injection.dll test_injection.c -luser32
   ```

### Automated Testing with Injection Script

1. First, start the Process Injection Detector:
   ```
   python run_detector.py
   ```

2. Then in another administrator command prompt, run the injection test:
   ```
   python inject_test.py
   ```

   The script will:
   - Find an existing notepad.exe process or start a new one
   - Inject the test_injection.dll into the process
   - The Process Injection Detector should detect and log this activity

### Expected Results

When you run the test script:

1. A notepad.exe window will open (if not already running)
2. A message box will appear from the injected DLL
3. The Process Injection Detector will log this as a suspicious activity
4. The event will be recorded in `detection_events.json`

### Manual Testing Options

If you prefer more control, you can also use other tools to inject the test DLL:

- **Process Hacker**: Open Process Hacker, right-click on a process, select "Miscellaneous" → "Inject DLL", and navigate to your test_injection.dll

### Safe Testing Practices

- Always test in a controlled environment
- The tests only inject into notepad.exe by default (a safe, non-critical process)
- Consider using a virtual machine for testing

## Output and Reporting

The tool generates several outputs:

1. **Console Output**: Real-time monitoring information and alerts
2. **Log File**: All activities are logged to `process_injection_detector.log`
3. **Detection Events**: Suspicious activities are saved to `detection_events.json` as structured data

Example alert:
```
⚠️ Potential Process Injection Detected!
Process: notepad.exe (PID: 1234)
Details: {'activities': ['Suspicious DLL location: C:\\path\\to\\test_injection.dll']}
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