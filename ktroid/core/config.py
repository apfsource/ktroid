import os
import json
from .utils import get_script_dir, print_warning

DEFAULT_CONFIG = {
    "java_version": "17",
    "agp_version": "8.13.2",
    "gradle_version": "9.3.1",
    "kotlin_version": "2.2.21",
    "compile_sdk": "35",
    "min_sdk": "21",
    "target_sdk": "35",
    "build_tools_version": "35.0.0"
}

def get_config_dir():
    return get_script_dir()

def load_config():
    config_path = os.path.join(get_config_dir(), "config.json")
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print_warning(f"Failed to load config file: {e}. Using defaults.")
    return config

CONFIG = load_config()

def save_config(new_config):
    config_path = os.path.join(get_config_dir(), "config.json")
    try:
        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=4)
        # Update current runtime config
        global CONFIG
        CONFIG.update(new_config)
        return True
    except Exception as e:
        print_warning(f"Failed to save config file: {e}")
        return False

def get_template_path(filename):
    return os.path.join(get_script_dir(), 'templates', filename)
