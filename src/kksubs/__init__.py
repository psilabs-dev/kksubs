from kksubs.service import project

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def add_subtitles(project_directory:str=None, drafts:Dict[str, List[int]]=None):
    logger.info("Adding subtitles.")
    return project.add_subtitles(project_directory=project_directory, drafts=drafts)
