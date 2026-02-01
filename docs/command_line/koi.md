# Koi Command Line Reference

`koi` is the unified command-line tool for managing Koikatsu Party subtitle projects. Application data is stored in `~/.kksubs`.

## Overview

Think of `koi` as a save file manager for Koikatsu Party with subtitle automation:
- **Library**: Collection of all your projects (like save files or game cartridges)
- **Project**: A named collection of game UserData + subtitle files (a specific save/cartridge)
- **Active Project**: The project currently loaded in your game directory and workspace
- **Game Directory**: Koikatsu installation where projects are loaded (like a cartridge player)
- **Workspace**: Subtitle processing layer that works on captures from the active project

When you "checkout" a project, it loads into both your game directory and workspace. The library stores backups of all projects.

---

## Configuration

### Configure
Configure application for the first time. Sets up game directory, library directory, and workspace directory.

```sh
koi configure
```

Interactive prompts will ask for:
- **Game directory**: Path to Koikatsu Party installation (contains `UserData/`)
- **Library directory**: Where to store project backups
- **Workspace directory**: Where subtitle files live (drafts, images, output)

### Info
Display current configuration and project information.

```sh
koi info
```

Show recent projects:
```sh
koi info --recent
```

### Version
Get application version.

```sh
koi version
```

---

## Project Management

Projects are stored in the library and can be loaded into your game directory. Think of them as save files that can be swapped in and out.

### List Projects
List all projects in the library.

```sh
koi archive list
```

Filter by pattern (supports wildcards):
```sh
koi archive list -p "story*"
koi archive list -p "genre/project-*"
```

Show recently accessed projects:
```sh
koi archive list --recent
```

### Create Project
Create a new project from the current game UserData state.

```sh
koi archive create <project-id>
```

Example:
```sh
koi archive create my-first-story
koi archive create action/beach-episode
```

This saves:
- Current game `UserData/` to `library/<project-id>/UserData/`
- Current workspace state to `library/<project-id>/kksubs-project/`

### Checkout Project
Load a project from the library into your game directory and workspace.

```sh
koi checkout <project-id>
```

Example:
```sh
koi checkout my-first-story
```

Create a new project from the current one (like `git checkout -b`):
```sh
koi checkout -b <new-project-id>
```

Example workflow:
```sh
# Create branch from current project
koi checkout -b story-1

# Work on story-1, then create another branch
koi checkout -b story-2

# Switch back to story-1
koi checkout story-1
```

### Rename Project
Rename the currently active project.

```sh
koi archive rename <new-project-id>
```

### Remove Project
Delete a project from the library.

```sh
koi archive remove <project-id>
```

**Warning**: This permanently deletes the project from the library.

---

## Synchronization

### Sync
Synchronize files between game directory, workspace, and library.

```sh
koi sync
```

This performs:
- Bidirectional sync: `game/UserData` ↔ `library/<current-project>/UserData`
- Unidirectional sync: `game/UserData/cap` → `workspace/images`
- Bidirectional sync: `workspace/` ↔ `library/<current-project>/kksubs-project/`

See [Architecture](../architecture.md) for detailed synchronization flow.

---

## Subtitle Operations

### Run
Execute subtitle processing on workspace images.

One-time run (sync + generate subtitles once):
```sh
koi run
```

Watch mode (continuously watch for changes and regenerate):
```sh
koi run --forever
```

In watch mode, subtitles automatically regenerate when:
- Draft files are modified
- Style file is changed
- New captures appear in game directory
- Images are deleted

Press Ctrl+C to stop watch mode.

### Show
Open the subtitled output folders in your system file explorer.

```sh
koi show
```

### Clear
Delete all generated subtitle outputs from the workspace.

```sh
koi clear
```

This removes all folders in `workspace/output/` (with confirmation prompt). Useful for starting fresh or troubleshooting.

---

## Advanced Operations

### Merge
Merge UserData content from another project into the currently loaded game directory.

```sh
koi merge <project-id>
```

Example:
```sh
koi merge story-2
```

This copies the following folders from the library project into your current game:
- `UserData/bg` (backgrounds)
- `UserData/cardframe`
- `UserData/chara` (characters)
- `UserData/coordinate` (outfits)
- `UserData/MaterialEditor`
- `UserData/Overlays`
- `UserData/studio` (scenes)

**Note**: Screenshots (`cap`) and save files are NOT merged. Files with the same name will be overridden.

**Use case**: Combine characters or scenes from different project branches.

Supports wildcards:
```sh
koi merge "story-*"
```

### Export
Export project galleries (captures and subtitled outputs) to a destination folder.

```sh
koi export
```

Exports:
- `UserData/cap` → `<destination>/cap`
- `kksubs-project/output` → `<destination>/output`

Destination is configured in `~/.kksubs/config.yaml` under `settings.export.destination`.

---

## Migrating from kkp

If you previously used the deprecated `kkp` CLI, here's the command mapping:

| Old kkp Command | New koi Command | Notes |
|-----------------|-----------------|-------|
| `kkp configure` | `koi configure` | Same |
| `kkp create <name>` | `koi archive create <name>` | Same functionality |
| `kkp list` | `koi archive list` | Same |
| `kkp checkout <name>` | `koi checkout <name>` | Same |
| `kkp checkout --branch <name>` | `koi checkout -b <name>` | Shorter flag |
| `kkp sync` | `koi sync` | Same |
| `kkp delete <name>` | `koi archive remove <name>` | Renamed to "remove" |
| `kkp compose` | `koi run` | Renamed to "run" |
| `kkp activate` | `koi run --forever` | Renamed to "run --forever" |
| `kkp show` | `koi show` | Same |
| `kkp clear` | `koi clear` | Same |
| `kkp merge <name>` | `koi merge <name>` | Same |
| `kkp export` | `koi export` | Same |
| `kkp game` | *(removed)* | Use scripts in `scripts/` directory |
| `kkp studio` | *(removed)* | Use scripts in `scripts/` directory |
| `kkp game-folder` | *(removed)* | Use scripts in `scripts/` directory |

Game launcher commands were removed. Use the shell scripts in `scripts/windows/` or `scripts/xdg/` instead by adding them to your PATH.

---

## Common Workflows

### Starting a New Story
```sh
# Create project from current game state
koi archive create my-story

# Work on subtitles
koi run --forever
```

### Creating Story Branches
```sh
# Create main story
koi archive create main-story

# Create branch for alternate ending
koi checkout -b alternate-ending

# Work on alternate ending...
# Switch back to main story
koi checkout main-story
```

### Merging Characters Between Projects
```sh
# You're working on story-1
koi checkout story-1

# Merge characters from story-2 into current game
koi merge story-2

# Create new merged project
koi archive create story-1-merged
```

---

## Configuration File

Configuration is stored in `~/.kksubs/config.yaml`:

```yaml
game-directory: C:\Games\Koikatsu Party
library-directory: C:\Users\...\library
workspace-directory: C:\Users\...\workspace
settings:
  export:
    destination: C:\Users\...\exports
  log:
    level: warning
```

Metadata is stored in `~/.kksubs/metadata/data.yaml`:

```yaml
current-project: genre/my-story
subtitle-sync-state: {...}
studio-sync-state: {...}
recent-projects: [...]
version: 3.2.0-dev
```
