 #!/usr/bin/env python
"""
DLL Injection Test Tool for Process Injection Detector

This tool automatically injects a test DLL into a target process to demonstrate
and test process injection detection capabilities. It's designed to work with
the Process Injection Detector and should be used for educational and testing
purposes only.

Features:
- Automatic target process selection (defaults to notepad.exe)
- Automatic process launching if target doesn't exist
- Full path resolution for the test DLL
- Clean error handling and user-friendly messages
- Proper resource cleanup

Usage:
    python inject_test.py [path_to_dll] [target_process]

Examples:
    python inject_test.py                      # Uses default DLL and notepad.exe
    python inject_test.py custom_test.dll      # Uses custom DLL and notepad.exe  
    python inject_test.py test.dll calc.exe    # Uses test.dll and calc.exe

Note: This script requires administrator privileges to work properly.
"""

import ctypes
import sys
import os
import time
import subprocess
from ctypes import windll, c_ulong, c_void_p, c_int, byref, sizeof, create_string_buffer
import psutil
import platform

# Constants for Windows API
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04
MEM_RELEASE = 0x8000
WAIT_OBJECT_0 = 0x00000000
INFINITE = 0xFFFFFFFF

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    """Print a nice banner for the tool"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.BOLD}{Colors.BLUE}╔══════════════════════════════════════════════════════╗{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}║                                                      ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}║  Process Injection Detector - Test Injection Tool    ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}║                                                      ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}╚══════════════════════════════════════════════════════╝{Colors.ENDC}")
    print()
    print(f"{Colors.WARNING}⚠️  For testing and educational purposes only{Colors.ENDC}")
    print(f"{Colors.WARNING}⚠️  This will inject code into a running process{Colors.ENDC}")
    print()

def print_status(message, status_type="info"):
    """Print a status message with appropriate formatting"""
    prefix = ""
    color = ""
    
    if status_type == "info":
        prefix = "[*]"
        color = Colors.BLUE
    elif status_type == "success":
        prefix = "[+]"
        color = Colors.GREEN
    elif status_type == "error":
        prefix = "[-]"
        color = Colors.FAIL
    elif status_type == "warning":
        prefix = "[!]"
        color = Colors.WARNING
        
    print(f"{color}{prefix} {message}{Colors.ENDC}")

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0  # Root check for Unix-like systems
    except Exception:
        return False

def find_or_start_target_process(target_name="notepad.exe"):
    """Find a suitable process to inject into, or start one if necessary"""
    target_name = target_name.lower()
    print_status(f"Looking for {target_name} process...")
    
    # Try to find the target process
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == target_name:
            print_status(f"Found existing {target_name} process (PID: {proc.info['pid']})", "success")
            return proc.info['pid']
    
    # No target process found, start one
    print_status(f"No running {target_name} found, starting a new instance...", "info")
    
    try:
        # Hide the window for cleaner execution
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen([target_name], startupinfo=startupinfo)
        time.sleep(1)  # Give process time to initialize
        
        if process.poll() is not None:  # Check if process is still running
            print_status(f"Failed to start {target_name}, process terminated unexpectedly", "error")
            return None
            
        print_status(f"Started {target_name} (PID: {process.pid})", "success")
        return process.pid
    except Exception as e:
        print_status(f"Error starting {target_name}: {e}", "error")
        return None

def inject_dll(pid, dll_path):
    """Inject a DLL into a process using classic DLL injection technique"""
    print_status(f"Preparing to inject {dll_path} into process with PID {pid}...")
    
    # Get process handle
    h_process = windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    
    if h_process == 0:
        print_status(f"Failed to open process {pid}: Access denied or invalid PID", "error")
        return False
    
    try:
        # Convert DLL path to bytes (ensuring it's full path)
        dll_path_abs = os.path.abspath(dll_path)
        dll_path_bytes = dll_path_abs.encode('ascii') + b'\0'
        path_len = len(dll_path_bytes)
        
        # Allocate memory for DLL path
        print_status("Allocating memory in target process...")
        remote_memory = windll.kernel32.VirtualAllocEx(
            h_process, 
            None, 
            path_len, 
            MEM_COMMIT | MEM_RESERVE, 
            PAGE_READWRITE
        )
        
        if remote_memory == 0:
            print_status("Failed to allocate memory in the target process", "error")
            return False
            
        # Write DLL path to process memory
        print_status("Writing DLL path to process memory...")
        written = c_int(0)
        result = windll.kernel32.WriteProcessMemory(
            h_process, 
            remote_memory, 
            dll_path_bytes, 
            path_len, 
            byref(written)
        )
        
        if result == 0:
            print_status("Failed to write to process memory", "error")
            return False
            
        # Get address of LoadLibraryA
        print_status("Locating LoadLibraryA function...")
        h_kernel32 = windll.kernel32.GetModuleHandleA(b"kernel32.dll")
        h_loadlib = windll.kernel32.GetProcAddress(h_kernel32, b"LoadLibraryA")
        
        if not h_loadlib:
            print_status("Failed to locate LoadLibraryA function", "error")
            return False
            
        # Create remote thread that calls LoadLibraryA(dll_path)
        print_status("Creating remote thread to execute LoadLibraryA...")
        thread_id = c_ulong(0)
        h_thread = windll.kernel32.CreateRemoteThread(
            h_process, 
            None, 
            0, 
            h_loadlib, 
            remote_memory, 
            0, 
            byref(thread_id)
        )
        
        if h_thread == 0:
            print_status("Failed to create remote thread", "error")
            return False
            
        print_status(f"Injection successful! Remote thread ID: {thread_id.value}", "success")
        
        # Wait for thread to complete
        print_status("Waiting for injection to complete...")
        wait_result = windll.kernel32.WaitForSingleObject(h_thread, 5000)  # Wait up to 5 seconds
        
        if wait_result != WAIT_OBJECT_0:
            print_status("Warning: Timeout waiting for thread completion", "warning")
        
        return True
        
    except Exception as e:
        print_status(f"Unexpected error during injection: {e}", "error")
        return False
        
    finally:
        # Clean up resources
        if 'remote_memory' in locals() and remote_memory != 0:
            windll.kernel32.VirtualFreeEx(h_process, remote_memory, 0, MEM_RELEASE)
            
        if 'h_thread' in locals() and h_thread != 0:
            windll.kernel32.CloseHandle(h_thread)
            
        if h_process != 0:
            windll.kernel32.CloseHandle(h_process)

def find_dll_path(custom_path=None):
    """Find the DLL to inject, using custom path or looking for default"""
    if custom_path:
        if os.path.exists(custom_path):
            return custom_path
        
        # Try to find in current directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, custom_path)
        if os.path.exists(full_path):
            return full_path
            
        print_status(f"Could not find DLL at path: {custom_path}", "error")
        return None
    
    # Look for default test_injection.dll
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_dll = os.path.join(script_dir, "test_injection.dll")
    
    if os.path.exists(default_dll):
        return default_dll
    
    print_status("Default test_injection.dll not found", "error")
    print_status("Please compile it first with one of these commands:")
    print_status("  cl.exe /LD test_injection.c user32.lib")
    print_status("  gcc -shared -o test_injection.dll test_injection.c -luser32")
    return None

def main():
    """Main entry point for the script"""
    print_banner()
    
    # Check for admin privileges
    if not is_admin():
        print_status("This script requires administrator privileges", "error")
        print_status("Please run it as administrator", "error")
        sys.exit(1)
    
    # Parse command line arguments
    dll_path = None
    target_process = "notepad.exe"
    
    if len(sys.argv) >= 2:
        dll_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        target_process = sys.argv[2]
    
    # Find the DLL
    dll_path = find_dll_path(dll_path)
    if not dll_path:
        sys.exit(1)
    
    print_status(f"Using DLL: {dll_path}", "info")
    print_status(f"Target process: {target_process}", "info")
    
    # Find or start target process
    pid = find_or_start_target_process(target_process)
    if not pid:
        print_status("Could not find or start target process", "error")
        sys.exit(1)
    
    # Perform the injection
    if inject_dll(pid, dll_path):
        print()
        print_status("Injection completed successfully", "success")
        print_status("Check the Process Injection Detector for alerts", "success")
    else:
        print()
        print_status("Injection failed", "error")
        sys.exit(1)

if __name__ == "__main__":
    main()