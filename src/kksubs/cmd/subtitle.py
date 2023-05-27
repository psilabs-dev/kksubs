import argparse
import logging

from kksubs.controller.subtitle import SubtitleController

log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

logger = logging.getLogger(__name__)

def command_line():
    
    parser = argparse.ArgumentParser(description="Command line tool for Koikatsu subtitling.")


    parser.add_argument('-p', '--project', default='.', help='Specify path to the project.')
    parser.add_argument('--log', default='warning', help='Set logging level.')
    parser.add_argument('-v', '--version', action='store_true', help='Get kksubs version.')

    subparsers = parser.add_subparsers(dest='command')

    init_parser = subparsers.add_parser('init', help='Initialize a project.')

    rename_parser = subparsers.add_parser('rename', help='Rename images in project.')

    activate_parser = subparsers.add_parser('activate', help='Compose subtitles continuously.')

    compose_parser = subparsers.add_parser('compose', help='Compose subtitles once.')

    for subparser in [activate_parser, compose_parser]:
        subparser.add_argument('-d', '--draft', default=None)
        subparser.add_argument('--disable-multiprocessing', action='store_true')
        subparser.add_argument('--incremental-update', action='store_true')
        subparser.add_argument('--prefix', default='')
        subparser.add_argument('--start', type=int, default=0)
        subparser.add_argument('--cap', type=int, default=200)

    clear_parser = subparsers.add_parser('clear', help='Clear project outputs.')
    clear_parser.add_argument('-f', '--force', action='store_true', help='Force clear without confirmation.')

    args = parser.parse_args()
    command = args.command

    controller = SubtitleController()
    project_directory = args.project
    controller.configure(project_directory)

    project_directory = args.project
    log_level = args.log

    log_level = 'info' if command == 'activate' else args.log
    logging.basicConfig(level=log_levels.get(log_level))

    get_version:bool = args.version
    if get_version:
        from kksubs.utils.import_utils import get_kksubs_version
        print(f'kksubs version {get_kksubs_version()}')
        return

    if command == 'init':
        controller.create()

    if command == 'rename':
        controller.rename()

    if command in {'activate', 'compose'}:
        disable_multiprocessing = args.disable_multiprocessing
        incremental_update = args.incremental_update
        draft = args.draft

        if draft is not None:
            draft = {draft:list(range(args.start, args.start+args.cap))}

        if command == 'activate':
            return controller.add_subtitles(
                drafts=draft, prefix=args.prefix, 
                allow_multiprocessing=True,
                allow_incremental_updating=True,
                watch=True
            )
        return controller.add_subtitles(
            drafts=draft, prefix=args.prefix, 
            allow_multiprocessing=not disable_multiprocessing,
            allow_incremental_updating=incremental_update,
            watch=False
        )

    if command == 'clear':
        controller.clear()

    if command is None:
        controller.info()

    controller.close()
    return