import logging
import os
import pkg_resources
import yaml

from common.utils.application import get_application_root, get_config_path

logger = logging.getLogger(__name__)

def show_application_version():
    KKSUBS_VERSION = pkg_resources.require('kksubs')[0].version
    print(KKSUBS_VERSION)
    return 0

def configure_application():
    logger.info("Configuring application...")

    # check if configs exist
    if os.path.exists(get_config_path()):
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
    if not os.path.exists(get_application_root()):
        os.makedirs(get_application_root())
    with open(get_config_path(), 'w', encoding='utf-8') as writer:
        yaml.safe_dump(config, writer)

    logger.info("Application configure success.")
    return 0