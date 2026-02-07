import json
import os
from pathlib import Path
from django.conf import settings

class DeviceManager:
    """
    Singleton class to manage devices using JSON file
    Shared across all apps
    """
    _instance = None
    _devices_file = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceManager, cls).__new__(cls)
            cls._devices_file = Path(settings.BASE_DIR) / 'devices.json'
            cls._instance._load_devices()
        return cls._instance
    
    def _load_devices(self):
        """
        Load devices from JSON file or create empty structure
        """
        try:
            # Check if file exists
            if not self._devices_file.exists():
                self.devices = {"admin_devices": [], "user_devices": []}
                self._save_devices()
            else:
                # Try to load existing file
                with open(self._devices_file, 'r') as f:
                    content = f.read().strip()
                    
                    # Check if file is empty
                    if not content:
                        self.devices = {"admin_devices": [], "user_devices": []}
                        self._save_devices()
                    else:
                        # Try to parse JSON
                        self.devices = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            # If JSON is corrupted, reset to default
            self.devices = {"admin_devices": [], "user_devices": []}
            self._save_devices()
    
    def _save_devices(self):
        """Save devices to JSON file"""
        with open(self._devices_file, 'w') as f:
            json.dump(self.devices, f, indent=2)
    
    def add_device(self, user_id, device_id, device_name, is_admin=False):
        """Add a new device entry"""
        device_data = {
            "device_id": device_id,
            "device_name": device_name,
            "user_id": user_id,
            "read_permission": True,
            "write_permission": False if not is_admin else True,
            "is_active": True
        }
        
        if is_admin:
            # Check if admin device already exists
            for device in self.devices["admin_devices"]:
                if device["device_id"] == device_id:
                    return False
            self.devices["admin_devices"].append(device_data)
        else:
            self.devices["user_devices"].append(device_data)
        
        self._save_devices()
        return True
    
    def remove_device(self, device_id):
        """Remove device when user signs out"""
        for device_list in [self.devices["admin_devices"], self.devices["user_devices"]]:
            for i, device in enumerate(device_list):
                if device["device_id"] == device_id:
                    device_list.pop(i)
                    self._save_devices()
                    return True
        return False
    
    def get_device(self, device_id):
        """Get device by ID"""
        for device_list in [self.devices["admin_devices"], self.devices["user_devices"]]:
            for device in device_list:
                if device["device_id"] == device_id:
                    return device
        return None
    
    def update_permission(self, device_id, read_permission=None, write_permission=None):
        """Update device permissions"""
        device = self.get_device(device_id)
        if device:
            if read_permission is not None:
                device["read_permission"] = read_permission
            if write_permission is not None:
                device["write_permission"] = write_permission
            self._save_devices()
            return True
        return False
    
    def list_devices(self):
        """List all devices"""
        all_devices = self.devices["admin_devices"] + self.devices["user_devices"]
        return all_devices
    
    def can_write(self, device_id):
        """Check if device has write permission"""
        device = self.get_device(device_id)
        if device:
            return device.get("write_permission", False)
        return False
    
    def can_read(self, device_id):
        """Check if device has read permission"""
        device = self.get_device(device_id)
        if device:
            return device.get("read_permission", True)
        return False