from kksubs.service import project

from typing import List
import logging

logger = logging.getLogger(__name__)

def add_subtitles(project_directory:str, draft_id:str, image_filters:List[int]=None):
    logger.info("Adding subtitles.")
    return project.add_subtitles(project_directory, draft_id, image_filters=image_filters)