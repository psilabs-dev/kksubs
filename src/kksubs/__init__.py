from typing import Dict, List

from kksubs.controller.subtitle import SubtitleController

# basic functions
def create_project(workspace_directory:str=None):
    return SubtitleController(workspace_directory=workspace_directory).create()

def rename_images(workspace_directory:str=None):
    return SubtitleController(workspace_directory=workspace_directory).rename()

def add_subtitles(
        workspace_directory:str=None, 
        allow_multiprocessing:bool=None,
        allow_incremental_updating:bool=None,
        watch:bool=None,
):
    if workspace_directory is None:
        workspace_directory = '.'
    return SubtitleController(workspace_directory=workspace_directory).add_subtitles(
        allow_multiprocessing=allow_multiprocessing,
        allow_incremental_updating=allow_incremental_updating, 
        watch=watch
    )

def clear_subtitles(workspace_directory:str=None):
    return SubtitleController(workspace_directory=workspace_directory).clear()