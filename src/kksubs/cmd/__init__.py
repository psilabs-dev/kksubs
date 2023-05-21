import argparse
import logging

# from kksubs import add_subtitles, clear_subtitles, create_project, rename_images
from kksubs.service.project import InvalidProjectException

log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

logger = logging.getLogger(__name__)

def kksubs_cmd():
    
    parser = argparse.ArgumentParser(description="Add subtitles to a kksubs project.")
    subparsers = parser.add_subparsers(dest='command')

    parser.add_argument('-p', '--project', default='.', help='Location of the project.')
    parser.add_argument('--log', default='warning')

    # initialize blank project
    init_parser = subparsers.add_parser('init', help='Initialize a project.')

    # rename images in project
    rename_parser = subparsers.add_parser('rename', help='Rename images in project.')

    activate_parser = subparsers.add_parser('activate', help='Run subtitling program continuously.')

    # compose subtitles
    compose_parser = subparsers.add_parser('compose', help='Compose subtitles for images.')

    # common arguments
    for subparser in [activate_parser, compose_parser]:
        subparser.add_argument('-d', '--draft', default=None)
        subparser.add_argument('--disable-multiprocessing', action='store_true')
        subparser.add_argument('--incremental-update', action='store_true')
        subparser.add_argument('--prefix', default='')
        subparser.add_argument('--start', type=int, default=0)
        subparser.add_argument('--cap', type=int, default=200)

    # clear project outputs
    clear_parser = subparsers.add_parser('clear', help='Clear project outputs.')
    clear_parser.add_argument('-f', '--force', action='store_true', help='Force clear without confirmation.')

    args = parser.parse_args()
    command = args.command

    project_directory = args.project
    log_level = args.log

    if isinstance(log_level, str) and log_level.lower() in log_levels:
        if command == 'activate':
            log_level = 'info'
        logging.basicConfig(level=log_levels[log_level.lower()])
    else:
        logger.warning(f"Invalid logging level selected: {log_level}")

    if command == 'init':
        create_project(project_directory)

    if command == 'rename':
        rename_images(project_directory)

    if command in {'activate', 'compose'}:
        disable_multiprocessing = args.disable_multiprocessing
        incremental_update = args.incremental_update
        draft = args.draft

        if draft is not None:
            draft = {draft:list(range(args.start, args.start+args.cap))}

        try:
            if command == 'activate':
                add_subtitles(
                    project_directory=project_directory, drafts=draft, prefix=args.prefix, 
                    allow_multiprocessing=True,
                    allow_incremental_updating=True,
                    watch=True
                )
                return
            add_subtitles(
                project_directory=project_directory, drafts=draft, prefix=args.prefix, 
                allow_multiprocessing=not disable_multiprocessing,
                allow_incremental_updating=incremental_update,
                watch=False
            )
            return
        
        except InvalidProjectException as exception:
            logger.error(f"Invalid kksubs project: {exception.project_directory}")
            return

    if command == 'clear':
        clear_subtitles(project_directory=project_directory, drafts=draft, force=args.f)

    if command is None:
        ...
