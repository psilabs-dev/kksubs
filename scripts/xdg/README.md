# XDG Scripts for Linux

Add this folder to your PATH to open folders with your default file manager. Make sure the scripts are executable.

Add environment variables for `KOIKATSU_PARTY_HOME` and `KKSUBS_LIBRARY`.

## Setup
Make the scripts executable:
```bash
chmod +x scripts/xdg/*
```

Add to your PATH (add to ~/.bashrc or ~/.zshrc):
```bash
export PATH="$PATH:/path/to/kksubs/scripts/xdg"
```

## Examples
Open captures folder:
```bash
cap
```

Open female character folder:
```bash
charaf
```

Open male character folder:
```bash
charam
```

Open kksubs library:
```bash
library
```

Open mods folder:
```bash
mods
```

Open studio scene folder:
```bash
scene
```

## Error Handling

All scripts include proper error handling:

- **Environment Variable Check**: Scripts will exit with error code 1 if the required environment variable is not set
- **Directory Existence Check**: Scripts will verify the target directory exists before attempting to open it

Example error messages:
```bash
$ cap
Error: KOIKATSU_PARTY_HOME environment variable is not set

$ library  
Error: KKSUBS_LIBRARY environment variable is not set

$ mods
Error: Directory does not exist: /path/to/koikatsu/mods
``` 