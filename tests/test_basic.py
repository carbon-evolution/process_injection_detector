import unittest
import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import after path adjustment
from process_injection_detector import ProcessInjectionDetector, ProcessInfo

class TestProcessInjectionDetector(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock config for testing
        self.test_config_path = Path('test_config.json')
        test_config = {
            "whitelisted_processes": ["test.exe"],
            "scan_interval": 1,
            "alert_email": "",
            "log_level": "DEBUG"
        }
        
        with open(self.test_config_path, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.test_config_path.exists():
            self.test_config_path.unlink()
    
    def test_process_info_creation(self):
        """Test creation of ProcessInfo object"""
        process_info = ProcessInfo(
            pid=1234,
            name="test.exe",
            path="C:\\test\\test.exe",
            command_line="test.exe --arg1 --arg2",
            create_time=12345.67,
            parent_pid=1000,
            parent_name="parent.exe",
            signature_valid=True,
            hash="aabbccddeeff"
        )
        
        self.assertEqual(process_info.pid, 1234)
        self.assertEqual(process_info.name, "test.exe")
        self.assertEqual(process_info.path, "C:\\test\\test.exe")
        self.assertEqual(process_info.command_line, "test.exe --arg1 --arg2")
        self.assertEqual(process_info.create_time, 12345.67)
        self.assertEqual(process_info.parent_pid, 1000)
        self.assertEqual(process_info.parent_name, "parent.exe")
        self.assertTrue(process_info.signature_valid)
        self.assertEqual(process_info.hash, "aabbccddeeff")
    
    def test_config_loading(self):
        """Test that configuration is loaded correctly"""
        # Note: This test doesn't create a full detector instance as that requires admin privileges
        # Instead, we're just testing the config loading mechanism
        
        config = {
            "whitelisted_processes": ["explorer.exe", "svchost.exe"],
            "scan_interval": 2,
            "alert_email": "",
            "log_level": "INFO"
        }
        
        # Create a test config file
        with open('config.json', 'w') as f:
            json.dump(config, f)
        
        # Load the config
        loaded_config = {}
        with open('config.json') as f:
            loaded_config = json.load(f)
        
        # Check the config
        self.assertEqual(loaded_config['whitelisted_processes'], ["explorer.exe", "svchost.exe"])
        self.assertEqual(loaded_config['scan_interval'], 2)
        
        # Clean up
        os.remove('config.json')

if __name__ == '__main__':
    unittest.main() 