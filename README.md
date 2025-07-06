# Koikatsu Automated Subtitles

![Tests](https://github.com/psilabs-dev/kksubs/actions/workflows/tests.yml/badge.svg)

> Command line tools to automate simple subtitle processing for Koikatsu stories.

**Basic function**: Given a folder of *images* and a text file called a *draft* (which contains a list of *subtitles* we want to apply to a specific image), the program will automatically apply each subtitle to its corresponding image, and save the subtitled images to an output directory.

![processed-image](demo.png)

## Installation and Setup
The program ~~is~~ *was* intended to work on a Windows OS with Python versions 3.10-3.12.
However, I can only test this on Ubuntu now.

Open a Python virtual environment and install the Git repository. For example:
```console
$ pip install git+https://github.com/psilabs-dev/kksubs.git
```
Configure the application:
```console
$ koi configure
```
Command line reference ([koi](docs\command_line\koi.md)).