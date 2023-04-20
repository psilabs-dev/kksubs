import logging
import os
import time
from typing import Dict, List
import traceback
import datetime

from kksubs.service.project import Project

logger = logging.getLogger(__name__)

class ProjectWatcher:

    def __init__(self, project:Project):
        # watch for changes in the project directory.
        self.project = project
        # sums the modified times to check for difference.
        # due to decimal precision of mod time, it is effectively unique.
        self.drafts_mtime_sum = None
        self.images_mtime_sum = None
        self.styles_mtime = None

    def detect_project_changes(self) -> bool:
        # check if draft has changed. Will trigger on startup and when one of the following has been changed.
        drafts_mtime_sum = sum(map(os.path.getmtime, [os.path.join(self.project.drafts_dir, draft) for draft in os.listdir(self.project.drafts_dir)]))
        images_mtime_sum = sum(map(os.path.getmtime, [os.path.join(self.project.images_dir, image) for image in os.listdir(self.project.images_dir)]))
        styles_mtime = None if not os.path.exists(os.path.join(self.project.project_directory, "styles.yml")) else os.path.getmtime(os.path.join(self.project.project_directory, "styles.yml"))

        changed_project = False

        changed_drafts = self.drafts_mtime_sum is None or self.drafts_mtime_sum != drafts_mtime_sum
        changed_images = self.images_mtime_sum is None or self.images_mtime_sum != images_mtime_sum
        changed_styles = (self.styles_mtime is None and styles_mtime is not None) or (styles_mtime is None and self.styles_mtime is not None) or (styles_mtime!=self.styles_mtime)

        if changed_drafts or changed_images or changed_styles:
            changed_project = True

        self.drafts_mtime_sum = drafts_mtime_sum
        self.images_mtime_sum = images_mtime_sum
        self.styles_mtime = styles_mtime

        return changed_project

    def watch(
            self, drafts:Dict[str, List[int]]=None, prefix:str=None, 
        allow_multiprocessing:bool=None,
        allow_incremental_updating:bool=None,
    ):

        try:
            logger.info("Watching project for changes.")
            while True:
                logger.debug("Scanning files.")
                try:
                    file_change_detected = self.detect_project_changes()

                    if file_change_detected:
                        logger.info("Project change detected, updating subtitles.")
                        self.project.add_subtitles(
                            drafts=drafts, prefix=prefix, 
                            allow_multiprocessing=allow_multiprocessing, 
                            allow_incremental_updating=allow_incremental_updating,
                            update_drafts=True,
                        )
                    else:
                        now = datetime.datetime.now().time().strftime('%H:%M:%S')
                        logger.info(f"{now} Scan complete: no changes detected.")
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception:
                    logger.error(f"An error occurred during scan cycle; retrying... Exception: {traceback.format_exc()}")

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Terminating watcher...")