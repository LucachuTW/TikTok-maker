"""Utils focused on detecting and connecting to the camera"""
import os
import pyudev
import yaml


def detect_cam():
    context = pyudev.Context()
    for device in context.list_devices(subsystem='usb'):
        if 'GoPro' in str(device):
            print("GoPro detectada:", device)

