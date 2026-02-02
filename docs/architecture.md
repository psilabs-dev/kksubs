# kksubs Architecture

This document describes the architecture and design principles of the kksubs subtitle automation system.

## Overview

kksubs is a Python-based subtitle automation tool for Koikatsu Party CharaStudio scenes. It manages projects (collections of game data and subtitle files) that can be versioned, branched, and merged like save files or game cartridges.

### Core Concepts

#### The Cartridge Analogy

Think of kksubs like a game console with swappable cartridges:

- **Library**: Your collection of game cartridges (all saved projects)
- **Project**: A single cartridge containing both game data and subtitle definitions
- **Game Directory**: The console itself (only holds one cartridge at a time)
- **Workspace**: The subtitle processor that works with captures from the loaded cartridge
- **Active Project**: The cartridge currently inserted in the console

When you "checkout" a project, you're swapping cartridges - the new project's data loads into both the game directory and workspace.

#### Components

**Library** (`~/library/`)
- Persistent storage for all projects
- Organized hierarchically: `library/genre/project-name/`
- Each project contains:
  - `UserData/` - Game assets (characters, scenes, backgrounds, captures)
  - `kksubs-project/` - Subtitle data (drafts, styles, outputs)

**Game Directory** (`C:\...\Koikatsu Party\`)
- Koikatsu Party installation
- Contains `UserData/` folder with currently loaded project data
- Only one project can be "loaded" at a time
- Captures are saved to `UserData/cap/`

**Workspace** (`~/workspace/`)
- Subtitle processing environment
- Structure:
  ```
  workspace/
  ├── images/          # Synced from game UserData/cap
  ├── drafts/          # Text files defining subtitles
  │   ├── draft-1.txt
  │   └── draft-2.txt
  ├── output/          # Generated subtitled images
  │   ├── draft-1/
  │   └── draft-2/
  └── styles.yml       # Style definitions
  ```

**Active Project**
- The project currently loaded in the game directory and workspace
- Stored in metadata: `~/.kksubs/metadata/data.yaml`
- Represents the "sharded" state across game and workspace

---

## Synchronization Architecture

The active project's state is distributed across three locations. Synchronization keeps them consistent.

### Synchronization Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Library                          │
│              (Persistent Backup)                    │
│                                                     │
│  genre/story-1/                                     │
│  ├── UserData/              ┌──────────────────┐    │
│  │   ├── bg/                │  Bidirectional   │    │
│  │   ├── chara/             │      Sync        │    │
│  │   ├── studio/            │                  │    │
│  │   └── cap/               │  Tracks changes  │    │
│  │                          │  via journal     │    │
│  └── kksubs-project/        │  (sync-state)    │    │
│      ├── drafts/            └──────────────────┘    │
│      ├── output/                                    │
│      └── styles.yml                                 │
└─────────────────────────────────────────────────────┘
            ▲                           ▲
            │                           │
            │ Bidirectional             │ Bidirectional
            │ Sync                      │ Sync
            │                           │
            ▼                           ▼
┌─────────────────────┐     ┌─────────────────────────┐
│  Game Directory     │     │     Workspace           │
│  (Currently Loaded) │     │  (Subtitle Processor)   │
│                     │     │                         │
│  UserData/          │     │   ~/workspace/          │
│  ├── bg/            │     │   ├── images/           │
│  ├── chara/         │     │   ├── drafts/           │
│  ├── studio/        │────────→│  ├── output/        │
│  └── cap/           │  │  │   └── styles.yml        │
│      └── *.png      │  │  │                         │
└─────────────────────┘  │  └─────────────────────────┘
                         │
                    Unidirectional
                    (cap → images)
                    Screenshots flow
                    one-way only
```

### Synchronization Types

**Bidirectional Sync** (`game/UserData` ↔ `library/UserData`)
- Changes in either location are mirrored to the other
- Uses journal-based tracking (`studio-sync-state` in metadata)
- Handles additions, modifications, and deletions
- Executed during `koi sync` and `koi checkout`

**Unidirectional Sync** (`game/UserData/cap` → `workspace/images`)
- Screenshots from game flow into workspace
- One-way only: workspace doesn't write back to game
- New captures automatically appear in workspace
- Executed during `koi sync` and `koi run`

**Bidirectional Sync** (`workspace/` ↔ `library/kksubs-project/`)
- Subtitle files (drafts, outputs, styles) sync both ways
- Uses journal-based tracking (`subtitle-sync-state` in metadata)
- Preserves work in both locations
- Executed during `koi sync` and `koi checkout`

### Synchronization Implementation

**Journal-Based Change Detection**
- Each sync operation records file states in metadata
- On next sync, compares current state to journal
- Uses set theory to identify: new files, modified files, deleted files
- Multiprocessing for batch operations

**Incremental Subtitle Updates**
- Only regenerates subtitles when inputs change:
  - Draft file modified
  - Style file modified
  - Source image changed
- Tracks state in workspace metadata (`.kksubs/` directory)
- Significantly faster than full regeneration

---

## Project Lifecycle

### Creating a Project

```sh
koi archive create my-story
```

1. Copies `game/UserData/` → `library/my-story/UserData/`
2. Copies `workspace/` → `library/my-story/kksubs-project/`
3. Updates metadata with project info
4. Records sync states

### Checking Out a Project

```sh
koi checkout my-story
```

1. Syncs current project back to library (if any)
2. Clears game `UserData/` directory
3. Copies `library/my-story/UserData/` → `game/UserData/`
4. Copies `library/my-story/kksubs-project/` → `workspace/`
5. Updates `current-project` in metadata
6. Records new sync states

### Branching a Project

```sh
koi checkout -b my-story-variant
```

1. Creates new project in library from current project
2. Names it `my-story-variant` (in same directory as parent)
3. Loads the new project into game and workspace
4. Both projects now exist independently in library

### Merging Projects

```sh
koi merge other-story
```

1. Prompts for confirmation
2. Copies specific UserData folders from `library/other-story/` → `game/`
3. Merged folders: `bg`, `chara`, `coordinate`, `MaterialEditor`, `Overlays`, `studio`
4. Excluded: `cap` (screenshots), `config`, `save`
5. Files with same names are overridden
6. Does NOT affect library - only current game directory

---

## Subtitle Processing Workflow

### One-Time Execution

```sh
koi run
```

1. **Sync**: Update workspace images from game captures
2. **Parse**: Read all draft files in `workspace/drafts/`
3. **Extract**: Parse `workspace/styles.yml` for style definitions
4. **Process**: For each draft:
   - Match subtitles to images
   - Apply styles (text, outlines, effects)
   - Render subtitled images
   - Save to `workspace/output/<draft-name>/`
5. **Sync**: Update library with new outputs

### Watch Mode

```sh
koi run --forever
```

Starts background watchers monitoring:
- `game/UserData/cap/` - New screenshots
- `workspace/drafts/` - Draft changes
- `workspace/styles.yml` - Style changes
- `workspace/images/` - Image additions/deletions

On change detected:
1. Run sync
2. Regenerate affected subtitles only (incremental)
3. Update library

Press Ctrl+C to stop.

---

## Image Processing Pipeline

### Core Libraries

- **Pillow**: Text rendering, composition, effects
- **OpenCV**: Advanced image operations, color space conversions
- **NumPy**: Array operations, transformations

### Processing Steps

For each subtitle:

1. **Load Image**: Read source PNG from workspace/images
2. **Parse Subtitle**: Extract text, position, style from draft
3. **Apply Style**: Retrieve style definition (with inheritance)
4. **Render Text**:
   - Load font (bundled Roboto or custom)
   - Create text layer with alpha channel
   - Apply stroke (outline)
5. **Apply Effects**:
   - Multiple outlines (feathered edges via blur)
   - Gaussian blur
   - Motion blur (directional)
   - Brightness adjustment
6. **Apply Box Transformations**:
   - Position via anchor coordinates or grid system
   - Rotation
   - Nudge (fine-tuning)
7. **Composite**:
   - Blend text onto image
   - Apply asset overlays (if any)
   - Apply masks (if any)
8. **Save**: Write to output directory

### Style System

Styles support:
- **Inheritance**: Styles can extend other styles
- **Matrix Multiplication**: Define style rows that combine (e.g., grid positions × text colors)
- **Per-Subtitle Overrides**: Individual subtitles can override any style property

See [Style Documentation](subtitle_project/styles.md) for details.

---

## Data Structures

### Configuration (`~/.kksubs/config.yaml`)

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

### Metadata (`~/.kksubs/metadata/data.yaml`)

```yaml
current-project: genre/my-story
subtitle-sync-state:
  # Journal of workspace ↔ library sync
  workspace/drafts/draft-1.txt: {mtime: 1234567890, hash: "..."}
  workspace/output/draft-1/image-1.png: {mtime: 1234567891, hash: "..."}
studio-sync-state:
  # Journal of game ↔ library sync
  UserData/chara/char-1.png: {mtime: 1234567892, hash: "..."}
  UserData/studio/scene-1.png: {mtime: 1234567893, hash: "..."}
recent-projects:
  - genre/my-story
  - action/beach-episode
  - ...
version: 3.2.0-dev
```

### Draft Format

Text-based format defining subtitles:

```
image_id: screenshot-001.png
content: Hello, world!
text_data.color: [255, 255, 255, 255]
box_data.anchor: [0, -200]

image_id: screenshot-002.png
content: |
  Multi-line
  subtitle text
style: custom-style-id
```

See [Draft Documentation](subtitle_project/draft.md) for syntax.

---

## Development Architecture

### Module Organization

```
src/
├── common/           # Shared utilities
│   ├── data/         # Serialization (RepresentableData)
│   ├── utils/        # File ops, coalesce, decorators
│   └── watcher/      # File watching abstraction
│
├── kkp/              # Project management
│   ├── controller/   # ProjectController (business logic)
│   ├── service/      # StudioProjectService (library ops)
│   ├── view/         # ProjectView (display)
│   └── watcher/      # ProjectWatcher (file watching)
│
├── kksubs/           # Subtitle processing
│   ├── controller/   # SubtitleController
│   ├── service/
│   │   ├── extraction/     # Parse drafts/styles
│   │   ├── processor/      # Image rendering
│   │   └── sub_project.py  # SubtitleProjectService
│   └── watcher/      # SubtitleWatcher
│
├── koi/              # CLI entry point
│   ├── cli.py        # Argument parsing
│   └── app/          # Application config
│
└── resources/        # Static assets (fonts)
```
