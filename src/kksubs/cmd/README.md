# commands

From the project root directory, add subtitles from `draft.txt` using the `kksubs-compose` command.

```
>>> kksubs-compose -d draft.txt
```
Add a `-p` flag to specify project path.
```
>>> kksubs-compose -p path/to/project -d draft.txt
```
Run the following to apply subtitles from all drafts.
```
>>> kksubs-compose
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
```
>>> kksubs-rename
```
will rename the images to
```
- 1.png
- 2.png
- 3.png
```
and populate the `draft.txt` draft:
```
image_id: 1.png

image_id: 2.png

image_id: 3.png
```