"""Utils focused on detecting and connecting to the camera"""
import pyudev

def detect_cam():
    context = pyudev.Context()
    for device in context.list_devices(subsystem='usb'):
        if 'GoPro' in str(device):
            print("GoPro detectada:", device)

