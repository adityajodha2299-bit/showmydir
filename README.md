# showmydir

A powerful CLI tool to visualize, export, and recreate directory structures with smart ignore rules.

## Features
- Tree View — Beautiful directory tree output
- Flat View — List files in a simple format
- Smart Ignore System
    - Built-in ignores (Python, Node, Git, etc.)
    - Custom ignore support
- `.smd` Format
    - Save directory structures
    - Recreate them anywhere
- Search Support (inside .smd)
- Fast & Lightweight
- Rich CLI output powered by rich

## Installation
### Using pipx (recommended)
```blash
pipx install showmydir
```

### Useing pip

```bash
pip install showmydir
```

## Usage
### Show directory tree
```
showmydir tree --root ./my_project
```

### Flat mode
```
showmydir tree --mode flat
```

### Save structure to `.smd`
```
showmydir tree --output project.smd
```

### Recreate structure from `.smd`
```
showmydir create-tree project.smd
```

## Ignore Options
Enable smart ignores:
```
showmydir tree --python --git --node
```

Available categories:
- `--python`
- `--node`
- `--git`
- `--docker`
- `--editor`
- `--rust`
- `--uv`

## How `.smd` Works

`.smd` is a lightweight format that stores directory structure.

- directory tree
- file structure
- metadata (size, counts, etc.)

You can:

- Save it
- Share it
- Recreate it anywhere

It allows you to recreate projects instantly **without scaning disk again and again**.

## Security
- All file and directory names are sanitized
- Prevents path traversal (e.g. ../)
- Safe to use for recreating directory structures


# Author

Aditya Pratap Singh Rathore

## License

MIT License © Aditya Pratap Singh Rathore