import argparse
import logging
import os

from kkp.controller.project import ProjectController

from koi.app.controller import configure_application, show_application_version

logger = logging.getLogger(__name__)

def cli():

    logging_level = os.getenv("KKSUBS_LOGGING_LEVEL")
    if logging_level == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    if logging_level == "INFO":
        logging.basicConfig(level=logging.INFO)
    if logging_level == "WARNING" or logging_level == "WARN":
        logging.basicConfig(level=logging.WARNING)
    if logging_level == "ERROR":
        logging.basicConfig(level=logging.ERROR)

    parser = argparse.ArgumentParser(description="Koi CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Version
    version_parser = subparsers.add_parser("version", help="Get version.")

    # Configure
    configure_parser = subparsers.add_parser("configure", help="Configure the application.")

    # Archive utilities
    archive_parser = subparsers.add_parser("archive", help="Archive commands")
    archive_subparsers = archive_parser.add_subparsers(dest='archive_command', required=True)
    
    archive_list_parser = archive_subparsers.add_parser("ls", aliases=['list'], help="List archived projects")
    archive_list_parser.add_argument("-r", "--recent", action="store_true", help="List recent projects")
    archive_list_parser.add_argument("-p", "--pattern", type=str, help="Pattern to match projects")

    archive_create_parser = archive_subparsers.add_parser("create", help="Create new archive from current project.")
    archive_create_parser.add_argument("project_id", type=str, help="Project ID")

    archive_remove_parser = archive_subparsers.add_parser("rm", aliases=['remove'], help="Remove archived project")
    archive_remove_parser.add_argument("project_id", type=str, help="Project ID")

    archive_rename_parser = archive_subparsers.add_parser("rename", help="Rename current project")
    archive_rename_parser.add_argument("new_project_id", type=str, help="New project ID")

    # Checkout
    checkout_parser = subparsers.add_parser("checkout", help="Checkout archived project")
    checkout_parser.add_argument("project_id", type=str, help="Project ID")
    checkout_parser.add_argument("-b", action="store_true", help="Optionally create new project from working one")

    # Run
    run_parser = subparsers.add_parser("run", help="Start a sync and subtitle session")
    run_parser.add_argument("--forever", action="store_true", help="Run indefinitely")

    # Sync
    sync_parser = subparsers.add_parser("sync", help="Sync files with remote archive")

    # Export
    export_parser = subparsers.add_parser("export", help="Export into a gallery")

    # Info
    info_parser = subparsers.add_parser("info", help="Show kksubs info")
    info_parser.add_argument("-r", "--recent", action='store_true', help="Show recent Projects.")

    # Show
    show_parser = subparsers.add_parser("show", help="Show subtitled images")

    args = parser.parse_args()
    command = args.command

    if command == "version":
        show_application_version()
        return
    if command == "configure":
        configure_application()
        return

    controller = ProjectController()
    controller.configure_v2()

    if command == "archive":
        archive_command = args.archive_command
        if archive_command in {"create"}:
            project_id = args.project_id
            controller.create(project_id)
        if archive_command in {"ls", "list"}:
            pattern = args.pattern
            controller.list_projects(pattern)
            pass
        if archive_command in {"rm", "remove"}:
            project_id = args.project_id
            controller.delete(project_id)
            pass
        if archive_command in {"rename"}:
            new_project_id = args.new_project_id
            controller.rename(new_project_id)
            pass
        # if archive_command is None:
        #     controller.info(show_recent_projects=True)
        #     pass

    if command == "info":
        is_recent = args.recent
        controller.info(show_recent_projects=is_recent)

    if command == "checkout":
        project_id = args.project_id
        is_new_project = args.b

        controller.checkout(project_id, new_branch=is_new_project)
        pass
    if command == "run":
        is_forever = args.forever

        if not is_forever:
            controller.compose(incremental_update=True)
        else:
            controller.activate()
    if command == "show":
        controller.open_output_folders()

        pass
    if command == "sync":
        controller.sync(compose=True)
        pass
    if command == "export":
        controller.export_gallery()
        pass

    controller.close()