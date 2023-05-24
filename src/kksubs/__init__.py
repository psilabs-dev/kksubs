from typing import Dict, List

from kksubs.controller.subtitle import SubtitleController

# basic functions
def create_project(project_directory:str=None):
    return SubtitleController(project_directory=project_directory).create()

def rename_images(project_directory:str=None):
    return SubtitleController(project_directory=project_directory).rename()

def add_subtitles(
        project_directory:str=None, 
        allow_multiprocessing:bool=None,
        allow_incremental_updating:bool=None,
        watch:bool=None,
):
    if project_directory is None:
        project_directory = '.'
    return SubtitleController(project_directory=project_directory).add_subtitles(
        allow_multiprocessing=allow_multiprocessing,
        allow_incremental_updating=allow_incremental_updating, 
        watch=watch
    )

def clear_subtitles(project_directory:str=None):
    return SubtitleController(project_directory=project_directory).clear()