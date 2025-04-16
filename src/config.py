"""
Configuration Management for ShiftPlan to ICS Converter

This module handles loading and saving application configuration.
"""

import os
import json
from pathlib import Path


# Default configuration
DEFAULT_CONFIG = {
    "nextcloud": {
        "url": "",
        "username": "",
        "password": "",
        "calendar": ""
    },
    "output_dir": os.path.join(".", "output"),
    "appearance": {
        "theme_name": "pink"
    }
}

# Determine the config file location
CONFIG_DIR = os.path.join(str(Path.home()), ".config", "shiftplan-to-ics")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_config_dir():
    """Ensure the configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR)
        except OSError as e:
            print(f"Warning: Could not create config directory: {e}")
            return False
    return True


def load_config():
    """Load configuration from the config file.
    
    Returns:
        dict: The loaded configuration or default if not found.
    """
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load config file: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to the config file.
    
    Args:
        config (dict): The configuration to save.
        
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    if not ensure_config_dir():
        return False
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError as e:
        print(f"Warning: Could not save config file: {e}")
        return False


def get_nextcloud_settings():
    """Get Nextcloud settings from config.
    
    Returns:
        dict: Nextcloud settings (url, username, password, calendar).
    """
    config = load_config()
    return config.get("nextcloud", DEFAULT_CONFIG["nextcloud"])


def save_nextcloud_settings(settings):
    """Save Nextcloud settings to config.
    
    Args:
        settings (dict): The Nextcloud settings to save.
        
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    config = load_config()
    config["nextcloud"] = settings
    return save_config(config)


def get_output_dir():
    """Get the output directory from config.
    
    Returns:
        str: The output directory path.
    """
    config = load_config()
    return config.get("output_dir", DEFAULT_CONFIG["output_dir"])


def save_output_dir(output_dir):
    """Save the output directory to config.
    
    Args:
        output_dir (str): The output directory path.
        
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    config = load_config()
    config["output_dir"] = output_dir
    return save_config(config)


def get_appearance_settings():
    """Get appearance settings from config.
    
    Returns:
        dict: Appearance settings (theme settings).
    """
    config = load_config()
    return config.get("appearance", DEFAULT_CONFIG["appearance"])


def save_appearance_settings(settings):
    """Save appearance settings to config.
    
    Args:
        settings (dict): The appearance settings to save.
        
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    config = load_config()
    config["appearance"] = settings
    return save_config(config) 