#!/usr/bin/env python
"""
Process Injection Detector Runner

This script provides a simple way to run the Process Injection Detector
directly from the root directory. It requires administrator privileges.
"""

import sys
import ctypes
import os

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def main():
    """Main entry point"""
    # Check for admin privileges
    if not is_admin():
        print("This script requires administrator privileges.")
        print("Please run it as administrator.")
        sys.exit(1)
    
    # Try to import and run the detector
    try:
        from process_injection_detector import main as detector_main
        detector_main()
    except ImportError:
        print("Could not import the Process Injection Detector module.")
        print("Make sure it's installed or in the correct directory.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDetector stopped by user.")
    except Exception as e:
        print(f"Error running detector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 