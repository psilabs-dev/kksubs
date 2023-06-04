# Koikatsu Automated Subtitles

![Tests](https://github.com/pain-text-format/kksubs/actions/workflows/tests.yml/badge.svg)

> Command line tools to automate simple subtitle processing for Koikatsu stories.

**Basic function**: Given a folder of *images* and a text file called a *draft* (which contains a list of *subtitles* we want to apply to a specific image), the program will automatically apply each subtitle to its corresponding image, and save the subtitled images to an output directory.

![processed-image](demo.png)

## Installation and Setup
The program is intended to work on a Windows OS with Python versions 3.8-3.11.

Open a Python virtual environment and install the Git repository. For example:
```console
$ pip install git+https://github.com/pain-text-format/kksubs.git
```

You can find an example project and usage [here](https://github.com/pain-text-format/kksubs-sample-project), and view [docs](docs/README.md) for more documentation.