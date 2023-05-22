import argparse
import logging

from kksubs.controller.project import ProjectController

from kksubs.exceptions import InvalidProjectException

log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

logging.basicConfig(level=logging.INFO) # debugging
logger = logging.getLogger(__name__)

# TODO: slowly stabilize and add back commands.
def command_line():

    parser = argparse.ArgumentParser()

    # necessary configuration data
    # search workspace for previous configuration details.
    # when run for the first time, will automatically create a kksubs project in the workspace and copy the contents of UserData captures over.
    parser.add_argument('--metadata', type=str, default='.', help='Specify directory to store metadata files.')
    parser.add_argument('--game-directory', type=str, help='Specify path to game directory.')
    parser.add_argument('--library', type=str, help='Specify path to library.')
    parser.add_argument('--workspace', type=str, help='Specify location for subtitle workspace.')

    subparsers = parser.add_subparsers(dest='command')

    compose_parser = subparsers.add_parser('compose', help='Compose subtitles once.')

    activate_parser = subparsers.add_parser('activate', help='Compose subtitles continuously.')

    clear_parser = subparsers.add_parser('clear', help='Clear subtitle outputs.')

    create_parser = subparsers.add_parser('create', help='Create a project.')
    create_parser.add_argument('project_name', type=str, help='Name of project to create.')

    list_parser = subparsers.add_parser('list', help='List projects.')
    list_parser.add_argument('-p', '--pattern', type=str)

    checkout_parser = subparsers.add_parser('checkout', help='Checkout a project from library.')
    checkout_parser.add_argument('project_name', type=str, help='Name of project to checkout.')

    delete_parser = subparsers.add_parser('delete', help='Delete a project or multiple projects')
    delete_parser.add_argument('project_name', type=str, help='Name of project to delete.')

    sync_parser = subparsers.add_parser('sync', help='Sync current project with library.')
    
    args = parser.parse_args()
    command = args.command

    controller = ProjectController()
    metadata_directory = args.metadata
    game_directory = args.game_directory
    library = args.library
    workspace = args.workspace
    controller.configure(metadata_directory, game_directory, library, workspace)

    # START SUBTITLE COMMANDS
    if command == 'compose':
        controller.compose()

    if command == 'activate':
        controller.activate()

    if command == 'clear':
        controller.clear()
    # END SUBTITLE COMMANDS

    # START PROJECT COMMANDS
    if command == 'create':
        project_name = args.project_name
        controller.create(project_name)

    if command == 'list':
        pattern = args.pattern
        controller.list_projects(pattern)

    if command == 'checkout': # a.k.a. assign
        project_name = args.project_name
        controller.checkout(project_name)

    if command == 'delete':
        project_name = args.project_name
        controller.delete(project_name)

    if command == 'sync':
        controller.sync()
    # END PROJECT COMMANDS

    if command is None:
        controller.info() # display information, version, current project

    controller.close()