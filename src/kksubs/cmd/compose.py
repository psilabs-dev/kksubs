import argparse

from typing import List

from kksubs import add_subtitles


def compose():
    
    parser = argparse.ArgumentParser(
        description="Add subtitles to a kksubs project."
    )
    parser.add_argument("-p", "--project", default=".")
    parser.add_argument("-d", "--draft", default=None)
    args = parser.parse_args()
    
    project_directory = args.project
    draft = args.draft

    if draft is not None:
        draft = {draft:None}

    add_subtitles(project_directory=project_directory, drafts=draft)