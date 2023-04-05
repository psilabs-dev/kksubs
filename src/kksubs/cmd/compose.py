import argparse
import logging
from typing import List

from kksubs import add_subtitles, clear_subtitles
from kksubs.service.project import InvalidProjectException

logger = logging.getLogger(__name__)

logging_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
}

def compose():
    
    parser = argparse.ArgumentParser(
        description="Add subtitles to a kksubs project."
    )
    parser.add_argument("-p", "--project", default=".")
    parser.add_argument("--prefix", default="")
    parser.add_argument("-d", "--draft", default=None)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--cap", type=int, default=200)
    parser.add_argument("--log", default=None)
    parser.add_argument("--disable-multiprocessing", action="store_true")
    parser.add_argument("--incremental-update", action="store_true")
    parser.add_argument("--watch", action="store_true")

    parser.add_argument("-c", "--clear", action="store_true")
    parser.add_argument("-cf", action="store_true") # clear directories without confirmation.
    args = parser.parse_args()
    
    project_directory = args.project
    prefix = args.prefix
    draft = args.draft
    start = args.start
    cap = args.cap
    clear = args.clear
    force_clear = args.cf
    logging_level = args.log
    allow_multiprocessing = not args.disable_multiprocessing
    incremental_update = args.incremental_update
    watch = args.watch

    # change logging on the command level.
    if logging_level is not None:
        if logging_level in logging_levels:
            logging.basicConfig(level=logging_levels.get(logging_level))
        else:
            raise KeyError(f"Invalid logging option: {logging_level}")

    if draft is not None:
        draft = {draft:list(range(start, start+cap))}

    if clear or force_clear:
        clear_subtitles(project_directory=project_directory, drafts=draft, force=force_clear)
        return 0

    try:
        add_subtitles(
            project_directory=project_directory, drafts=draft, prefix=prefix, 
            allow_multiprocessing=allow_multiprocessing,
            allow_incremental_updating=incremental_update,
            watch=watch
        )
        return 0
    except InvalidProjectException as exception:
        logger.error(f"Invalid kksubs project: {exception.project_directory}")
        return 1