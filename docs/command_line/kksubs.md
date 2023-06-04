# KKSUBS Command Line Tool

`kksubs` (Koikatsu Subtitles) is a command line tool that adds subtitles to images.

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
```bash
kksubs --project [project-directory] compose
kksubs --project [project-directory] activate
kksubs --project [project-directory] clear
```
Like `kkp`, `kksubs` is also equipped with `compose`, `activate` and `clear` commands, which serve the same purpose. Since there is no game directory, `activate` will not search for changes there.
