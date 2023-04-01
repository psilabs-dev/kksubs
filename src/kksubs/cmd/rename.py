import argparse

from kksubs import rename_images

def rename():
    
    parser = argparse.ArgumentParser(
        description="Rename images and apply filename changes to drafts."
    )
    parser.add_argument("-p", "--project", default=".")
    args = parser.parse_args()

    project_directory = args.project
    rename_images(project_directory)