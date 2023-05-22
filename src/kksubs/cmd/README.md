# command line tool

Command line tools.

* `kkp`: for subtitling images and general project management in an integrated environment.
* `kksubs`: for only subtitling images.

# KK Projects/`kkp`

`kkp` is a subtitling/project management tool for Koikatsu projects. Requires prior configuration to run successfully.

## Initialize
```bash
kkp --workspace [workspace] --game [game-directory] --library [library-directory]
```
Initializes the `kksubs` project. Configuration lives in `kksubs.yaml` file.

The `[game-directory]` is the game directory which contains the `UserData` folder. The `[workspace]` is the folder where subtitle-related objects go (e.g. `images`, `output`, `drafts`, `styles.yml`).

---
## Create Project
```bash
kkp create [project-name]
```
Makes a copy of `UserData` in the game directory into the library, and also copies the renders in `UserData/cap` to `[workspace]/images`. This is known as the "current project". Additionally, creates a `kksubs` subtitling project:
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
Continuously watch the `[workspace]` for changes, and apply subtitles as files in the `[workspace]` change. Furthermore, uses incremental updating to process only images whose image, subtitle or style has changed, accelerating the subtitling process. 

Persistent data used to accelerate subtitling is stored in the `[workspace]/.kksubs` directory. This is not necessary to add subtitles, but enables incremental updating.

## Clear 
```bash
kksubs clear
```
Delete outputs and the `.kksubs` directory within the workspace.

# KK Subtitles/`kksubs`
`kksubs` is exclusively a subtitling tool. Does not require prior configuration, nor a game directory. Separate from `kkp`.

## Initialize Subtitle Project
```bash
kksubs --project [project-directory] init
```
Create a blank subtitling project with structure
```
- images
- drafts
- output
- styles.yml
```
Does not override existing project structure. Defaults to current directory.

## Rename
```bash
kksubs --project [project-directory] rename
```
Renames the images in the `images` directory. Also renames the image keys in any draft.

## Activate/Compose/Clear
```
kksubs --project [project-directory] compose
kksubs --project [project-directory] activate
kksubs --project [project-directory] clear
```
Like `kkp`, `kksubs` is also equipped with `compose`, `activate` and `clear` commands, which serve the same purpose.
