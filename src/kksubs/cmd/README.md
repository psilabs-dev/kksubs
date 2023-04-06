# commands
> Documentation for some terminal commands in `kksubs`.

## Add and remove subtitles

From the project root directory, add subtitles from `draft.txt` using the `kksubs-compose` command.

```console
$ kksubs-compose -d draft.txt
```
Specify project path using the `--project` or `-p` flag.
```console
$ kksubs-compose -p path/to/project -d draft.txt
```
Run the following to apply subtitles from all drafts.
```console
$ kksubs-compose
```
Add a `--prefix` to add a prefix.
```console
$ kksubs-compose --prefix "subbed-"
```
Use `--start` and `--cap` to control the range of images to subtitle. For example, to subtitle the first 20 images after the image at index 15 (note: indices start at 0):
```console
$ kksubs-compose -d draft.txt --cap 20 --start 15
```

Clear/remove all subtitled images in the output directory using the `--clear` or `-c` flag.
```console
$ kksubs-compose --clear
```
Clear a specific directory, such as `output/draft`.
```console
$ kksubs-compose --clear -d draft
```
Force clear a directory without a confirmation step.
```console
$ kksubs-compose -cf
```

## Renaming images
Use the `kksubs-rename` command to rename/standardize images in the `images` directory, and apply the filename changes to every draft in the `drafts` directory.

Suppose the image directory looks like this:
```
- charastudio-render-1.png
- charastudio-render-2.png
- charastudio-render-3.png
```
And the `draft.txt` file is empty. Running
```console
$ kksubs-rename
```
will rename the images to
```
- 1.png
- 2.png
- 3.png
```
and populate the `draft.txt` draft with empty subtitles:
```
image_id: 1.png

image_id: 2.png

image_id: 3.png
```

## Optimization: multiprocessing and incremental updating
Multiprocessing is enabled by default to accelerate the subtitling process across multiple CPU cores. To disable multiprocessing, run
```console
$ kksubs-compose --disable-processing
```
Incremental updating is a feature which tells the program to only update subtitles that have been changed. Factors involved include changes in the draft, changes in `styles.yml`, or changes in the images directory. This forms a "snapshot" which is then compared with the next time you run `kksubs-compose`. This will accelerate subtitling, especially if you have hundreds of images and only changed a few lines.

Incremental updating relies on the `pickle` library to serialize/deserialize objects, which can be insecure. Ensure that the `.kksubs` directory does not contain untrusted files.

This is a personally developed feature and can be buggy, so it is not enabled by default. To enable incremental updating, use the `--incremental-update` flag.

```console
$ kksubs-compose --incremental-update
```

## Run kksubs as a continuous process
You can run `kksubs` as a continuous process, so you may focus working on editing subtitles and viewing results. This is done with the `--watch` flag.
```console
$ kksubs-compose --watch
```
This sets up a project watcher, which keeps "watch" of the drafts and images directory, and also the `styles.yml` file if there exists one. When a change is detected in these watch targets, the watcher will trigger a request to subtitle the images. This process occurs once per second.

