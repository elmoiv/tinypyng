# TinyPyng
Compress pictures using [tinypng.com](https://tinypng.com/) without API token

## Features
- ***No API Token required***
- Can compress files recursively
- Powerful options

## Usage
```console

> python tinypyng.py --help

usage: tinypyng.py [-h] -p PATH [-r] [-o OUTPUT]

Argument parser for tinypy

required arguments:
  -p PATH, --path PATH  PNG or JPG file, Directory of PNGs, txt file of paths

optional arguments:
  -r, --recursive       Recursively compress the photo to the maximum possible
                        limit
  -o OUTPUT, --output OUTPUT
                        Custom folder to store compressed pictures
```

## Examples
```console
// Compress a single png
> python tinypyng.py -p "path\\to\\file.png"

// Compress a single png recursively
> python tinypyng.py -p "path\\to\\file.png" -r

// Compress all pictures inside folder
> python tinypyng.py -p "path\\to\\folder\\"

// Compress all pictures from a .txt file
> python tinypyng.py -p "path\\to\\file.txt"

// Compress all pictures inside folder recursively and
// store them in custom folder
> python tinypyng.py -p "path\\to\\folder\\" -r -o "path\\to\\custom_folder\\"
```
## Contributing
Please contribute! If you want to fix a bug, suggest improvements, or add new features to the project, just [open an issue](https://github.com/elmoiv/tinypyng/issues) or send me a pull request.
