import ctypes
import psutil
import time
import logging
import json
import os
import sys
import win32api
import win32con
import win32security
import win32process
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path
import threading
import queue
import hashlib
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_injection_detector.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class ProcessInfo:
    pid: int
    name: str
    path: str
    command_line: str
    create_time: float
    parent_pid: int
    parent_name: str
    signature_valid: bool
    hash: str

@dataclass
class InjectionEvent:
    timestamp: str
    process_info: ProcessInfo
    injection_type: str
    suspicious_dll: str
    additional_info: Dict

class ProcessInjectionDetector:
    def __init__(self):
        self.kernel32 = ctypes.WinDLL("kernel32.dll")
        self.psapi = ctypes.WinDLL("Psapi.dll")
        self.ntdll = ctypes.WinDLL("ntdll.dll")
        
        # Initialize configuration
        self.config = self.load_config()
        self.whitelist = set(self.config.get('whitelisted_processes', []))
        self.scan_interval = self.config.get('scan_interval', 2)
        
        # Initialize caches
        self.process_cache: Dict[int, ProcessInfo] = {}
        self.known_signatures: Dict[str, bool] = {}
        
        # Event queue for detected injections
        self.event_queue = queue.Queue()
        
        # Ensure running with admin privileges
        self.check_privileges()

    def load_config(self) -> dict:
        """Load configuration from config.json file"""
        config_path = Path('config.json')
        if not config_path.exists():
            default_config = {
                'whitelisted_processes': ['explorer.exe', 'svchost.exe'],
                'scan_interval': 2,
                'alert_email': '',
                'log_level': 'INFO'
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        
        with open(config_path) as f:
            return json.load(f)

    def check_privileges(self):
        """Ensure the script is running with administrator privileges"""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                logging.error("This script requires administrator privileges!")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Failed to check privileges: {e}")
            sys.exit(1)

    def get_process_info(self, pid: int) -> ProcessInfo:
        """Gather detailed information about a process"""
        try:
            process = psutil.Process(pid)
            path = process.exe()
            
            # Get process signature information
            signature_valid = self.verify_signature(path)
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(path)
            
            return ProcessInfo(
                pid=pid,
                name=process.name(),
                path=path,
                command_line=' '.join(process.cmdline()),
                create_time=process.create_time(),
                parent_pid=process.ppid(),
                parent_name=psutil.Process(process.ppid()).name(),
                signature_valid=signature_valid,
                hash=file_hash
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.debug(f"Could not get process info for PID {pid}: {e}")
            return None

    def verify_signature(self, file_path: str) -> bool:
        """Verify digital signature of a file"""
        if file_path in self.known_signatures:
            return self.known_signatures[file_path]
        
        try:
            return win32api.VerifySignature(file_path)
        except Exception as e:
            logging.debug(f"Failed to verify signature for {file_path}: {e}")
            return False

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logging.debug(f"Failed to calculate hash for {file_path}: {e}")
            return ''

    def detect_classic_injection(self, process: psutil.Process) -> List[str]:
        """Detect classic injection techniques"""
        suspicious_activities = []
        
        try:
            # Check for suspicious memory regions
            for mmap in process.memory_maps():
                if mmap.path.endswith('.dll'):
                    # Check if DLL is loaded from suspicious location
                    if any(sus_path in mmap.path.lower() for sus_path in ['temp', 'downloads']):
                        suspicious_activities.append(f"Suspicious DLL location: {mmap.path}")
                
                # Check for memory regions with suspicious permissions
                if 'rwx' in mmap.perms:
                    suspicious_activities.append(f"Suspicious memory permissions: {mmap.perms}")
        except Exception as e:
            logging.debug(f"Failed to check memory maps for PID {process.pid}: {e}")
        
        return suspicious_activities

    def detect_process_hollowing(self, process: psutil.Process) -> List[str]:
        """Detect process hollowing techniques"""
        suspicious_activities = []
        
        try:
            # Check for unmapped PE header
            with open(process.exe(), 'rb') as f:
                header = f.read(2)
                if header != b'MZ':
                    suspicious_activities.append("Suspicious PE header modification")
            
            # Check for suspicious thread start addresses
            for thread in process.threads():
                # Implementation specific to your needs
                pass
                
        except Exception as e:
            logging.debug(f"Failed to check for process hollowing in PID {process.pid}: {e}")
        
        return suspicious_activities

    def monitor_processes(self):
        """Main monitoring loop"""
        logging.info("🔍 Starting Process Injection Monitoring...")
        
        while True:
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] in self.whitelist:
                        continue
                    
                    try:
                        process_info = self.get_process_info(proc.info['pid'])
                        if not process_info:
                            continue
                        
                        # Check for various injection techniques
                        suspicious_activities = []
                        suspicious_activities.extend(self.detect_classic_injection(proc))
                        suspicious_activities.extend(self.detect_process_hollowing(proc))
                        
                        if suspicious_activities:
                            event = InjectionEvent(
                                timestamp=datetime.now().isoformat(),
                                process_info=process_info,
                                injection_type="Multiple",
                                suspicious_dll="",
                                additional_info={"activities": suspicious_activities}
                            )
                            self.event_queue.put(event)
                            self.handle_detection(event)
                            
                    except Exception as e:
                        logging.debug(f"Error processing PID {proc.info['pid']}: {e}")
                        
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                
            time.sleep(self.scan_interval)

    def handle_detection(self, event: InjectionEvent):
        """Handle detected injection events"""
        # Log the event
        logging.warning(f"⚠️ Potential Process Injection Detected!")
        logging.warning(f"Process: {event.process_info.name} (PID: {event.process_info.pid})")
        logging.warning(f"Details: {event.additional_info}")
        
        # Save to JSON file
        self.save_event(event)
        
        # Implement additional actions (email alerts, SIEM integration, etc.)
        self.alert_admin(event)

    def save_event(self, event: InjectionEvent):
        """Save detection event to JSON file"""
        events_file = Path('detection_events.json')
        events = []
        
        if events_file.exists():
            with open(events_file) as f:
                events = json.load(f)
        
        events.append(asdict(event))
        
        with open(events_file, 'w') as f:
            json.dump(events, f, indent=4)

    def alert_admin(self, event: InjectionEvent):
        """Send alert to administrator"""
        # Implement your alerting mechanism here (email, Slack, etc.)
        pass

def main():
    try:
        detector = ProcessInjectionDetector()
        detector.monitor_processes()
    except KeyboardInterrupt:
        logging.info("\n👋 Stopping Process Injection Detector...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 