# showmydir

A powerful CLI tool to visualize and recreate directory structures.

## Features
- Tree, flat, and JSON view modes
- Smart ignore system
- Custom `.smd` format
- Dry-run preview for safe directory creation

## Installation
```bash
pip install showmydir
```

or use pipx (recommended)

```bash
pipx install showmydir
```

## Usage
To view a directory tree:
```
showmydir tree --root ./my_project
```

## What is `.smd`?

`.smd` (ShowMyDir format) is a JSON-based structure that stores:

- directory tree
- file structure
- metadata (size, counts, etc.)

It allows you to recreate projects instantly **without scaning disk again and again**.

# Author

Aditya Pratap Singh Rathore

## License

MIT License — see LICENSE