# KKP Command Line Tool

`kkp` (Koikatsu Projects) is a command line tool that integrates subtitle projects with the Koikatsu Party game in a more integrated environment. 

A "studio project" refers to the subtitle project along with the `UserData` folder it is associated with. `kkp` is thus a manager of studio projects.

Main features:

* Create a subtitle project from the current game directory
    * Add subtitles on images in the `UserData/cap` folder
* Save/load multiple studio projects to/from a library

## Configure
```bash
kkp --workspace [workspace] --game [game-directory] --library [library-directory]
```

Configures the `kkp` command line tool. Configuration is stored in `[working-directory]/config.yaml`, while data is stored in `[working-directory]/data.yaml`.

The `[game-directory]` is the game directory which contains the `UserData` folder. The `[workspace]` is the folder where subtitle-related objects go (e.g. `images`, `output`, `drafts`, `styles.yml`).

### Example
```
kkp --workspace workspace --game "C:\Users\user\Games\Koikatsu Party" --library library
```

---
## Create Project
```bash
kkp create [project-name]
```
Makes a copy of `UserData` in the game directory into the library, and also copies the renders in `UserData/cap` to `[workspace]/images`. This is known as the "current project". Additionally, creates a subtitle project:
```
- [workspace]
    - images
        - # the captures from the game directory's UserData/cap
    - drafts
    - output
    - styles.yml
```

## List Projects
```bash
kkp list -p [pattern]
# [0] project-1
# [1] project-2
# ...
```
List valid projects found in the `[library]`. The list can be filtered with a pattern using wildcards.

## Synchronize
Saves and synchronizes files between the `[game]`, `[library]`, and `[workspace]`. In arrows (one-way and two-way sync resp.):

```
[game]/UserData <==> [library]/[current-project]/UserData
[library]/[current-project]/UserData/cap ==> [workspace]/images

[workspace]/drafts <==> [library]/[current-project]/kksubs-project/drafts
[workspace]/output <==> [library]/[current-project]/kksubs-project/output
[workspace]/styles.yml <==> [library]/[current-project]/kksubs-project/styles.yml
```

## Checkout Project
```bash
kkp checkout [project-name]
```
Change the current project to another project in the library. This replaces the game directory's `UserData` with the one found under `[library]/[project-name]`. This also replaces the items in the subtitle workspace with the ones found under `[library]/[project-name]/kksubs-project`.

Checkout to a new project from the current one like git. (This will create a project in the same directory as the current project.)
```bash
kkp checkout --branch [project-name]
```
Combine `list` and `checkout` to checkout based on numbers.
```bash
kkp list -p *world*
# [0] hello/world
kkp checkout 0
# checkout project hello/world
```

## Execute Programs/Open Folders

```
kkp game
```
Run Koikatsu Party.
```
kkp studio
```
Run Chara Studio.
```
kkp game-folder
```
Open Koikatsu Party folder with explorer.
```
kkp show
```
Open subtitled image folders with explorer.

## Delete Project
```bash
kkp delete [project-name]
```
Delete project with name `[project-name]` from the library.

If the current project is to be deleted, the contents of the workspace will be deleted too.

## Compose/Activate
```bash
kkp compose
```
Create subtitled images once. The images are saved in the `output` directory.
```bash
kkp activate
```
Continuously watch the `[workspace]` and `[game]/UserData/cap` for changes, and applies two actions as observed files change:

1. runs `kkp sync`
2. runs `kkp compoose`

Furthermore, uses incremental updating to process only images whose image, subtitle or style has changed, accelerating the subtitling process. 

Persistent data used to accelerate subtitling is stored in the `[workspace]/.kksubs` directory. This is not necessary to add subtitles, but enables incremental updating.

## Clear 
```bash
kkp clear
```
Delete outputs and the `.kksubs` directory within the workspace.

## Merge
```
kkp merge [project-name]
```
Merge `UserData` contents of another project (or projects if you use wildcards) into the current one. Existing files will not be deleted, but files with the same names will be overridden.

Affected folders include:

* bg
* cap
* cardframe
* chara
* coordinate
* MaterialEditor
* Overlays
* studio

## Export
```
kkp export [--clean] [--show] [--force] [export-destination]
```
Export outputs (`UserData/cap` and `kksubs-project/output`) of projects to a destination folder.

`clean` flag deletes the destination folder and creates a new one.

`show` flag opens the destination folder in file explorer after exporting.

`force` flag disables confirmation prompts.