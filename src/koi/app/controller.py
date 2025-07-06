import logging
import os
import importlib.metadata
import yaml

from common.utils.application import get_application_root, get_config_path

logger = logging.getLogger(__name__)

def show_application_version():
    KKSUBS_VERSION = importlib.metadata.version('kksubs')
    print(KKSUBS_VERSION)
    return 0

def configure_application():
    logger.info("Configuring application...")

    # check if configs exist
    if get_config_path().exists():
        # confirm override.
        confirm_override = input("Config exists. Override? (y): ")
        if confirm_override != "y":
            return 0

    # get user input
    game_directory = input("Enter game directory: ")
    library_directory = input("Enter library directory: ")
    workspace_directory = input("Enter workspace directory: ")

    # check that user input is valid
    if not (os.path.exists(game_directory)):
        logger.error(f"Game directory {game_directory} does not exist. Exiting...")
        return 1
    else:
        game_directory = os.path.realpath(game_directory)
    if not (os.path.exists(library_directory)):
        logger.error(f"Data directory {library_directory} does not exist. Exiting...")
        return 1
    else:
        library_directory = os.path.realpath(library_directory)
    if not (os.path.exists(workspace_directory)):
        logger.error(f"Data directory {library_directory} does not exist. Exiting...")
        return 1
    else:
        workspace_directory = os.path.realpath(workspace_directory)

    # write config into dotfile.
    config = {
        "game-directory": game_directory,
        "library-directory": library_directory,
        "workspace-directory": workspace_directory,
    }
    app_root = get_application_root()
    if not app_root.exists():
        app_root.mkdir(parents=True, exist_ok=True)
    with open(get_config_path(), 'w', encoding='utf-8') as writer:
        yaml.safe_dump(config, writer)

    logger.info("Application configure success.")
    return 0