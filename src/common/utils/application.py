import pathlib

# common application related functions.

def __get_home_directory() -> pathlib.Path:
    return pathlib.Path.home()

def get_application_root() -> pathlib.Path:
    return __get_home_directory() / ".kksubs"

def get_config_path() -> pathlib.Path:
    return __get_home_directory() / "config.yaml"

def get_data_filepath() -> pathlib.Path:
    return __get_home_directory() / "kksubs.yaml"
