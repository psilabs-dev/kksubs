import os

# common application related functions.

def get_home_directory() -> str:
    return os.path.expanduser("~")

def get_application_root() -> str:
    return os.path.join(get_home_directory(), ".kksubs")

def get_config_path() -> str:
    return os.path.join(get_application_root(), "config.yaml")

def get_data_filepath() -> str:
    return os.path.join(get_application_root(), "kksubs.yaml")

