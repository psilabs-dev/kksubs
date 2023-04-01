from kksubs.service.project import Project
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def rename_images(project_directory:str=None):
    logger.info("Renaming images.")
    return Project(project_directory=project_directory).rename_images()

def add_subtitles(project_directory:str=None, drafts:Dict[str, List[int]]=None, prefix:str=None):
    logger.info("Adding subtitles.")
    return Project(project_directory=project_directory).add_subtitles(drafts=drafts, prefix=prefix)

def clear_subtitles(project_directory:str=None, drafts:Dict[str, List[int]]=None, force=False):
    logger.info("Clearing subtitles.")
    return Project(project_directory=project_directory).clear_subtitles(drafts=drafts, force=force)