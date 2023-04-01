import argparse

from typing import List

from kksubs import add_subtitles, clear_subtitles


def compose():
    
    parser = argparse.ArgumentParser(
        description="Add subtitles to a kksubs project."
    )
    parser.add_argument("-p", "--project", default=".")
    parser.add_argument("--prefix", default="")
    parser.add_argument("-d", "--draft", default=None)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--cap", type=int, default=200)

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

    if draft is not None:
        draft = {draft:list(range(start, start+cap))}

    if clear or force_clear:
        clear_subtitles(project_directory=project_directory, drafts=draft, force=force_clear)
    else:
        add_subtitles(project_directory=project_directory, drafts=draft, prefix=prefix)
        