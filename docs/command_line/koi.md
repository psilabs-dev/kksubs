# Koi Command Line Reference

Command line tool for `kksubs`. Application data is stored in `~\.kksubs`.

## Configure
Configure application for the first time.
```sh
koi configure
```

## Archive
Archive (aka Project) related tools.
### List Archives
List archives.

```sh
koi archive list
```

### Create Archive
Create an archive.
```sh
koi archive create <project-id>
```

### Remove Archive
Remove an archive.
```sh
koi archive remove <project-id>
```

### Rename Archive
Rename an archive.
```sh
koi archive rename <new-project-id>
```

## Checkout
Switch to a different archive.
```sh
koi checkout [-b] <project-id>
```

## Run
Run `kksubs` subtitling program.
```sh
koi run [--forever]
```

## Show
Open subtitled output images in File Explorer.
```sh
koi show
```

## Sync
Sync with archive
```sh
koi sync
```

## Export
Export project galleries to a folder.
```sh
koi export
```

## Version
Get application version.
```sh
koi version
```