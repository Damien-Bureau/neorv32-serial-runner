# NEORV32 Serial Runner

A user-friendly tool to easily upload and run compiled binary files onto a NEORV32 processor via a serial communication port.

## Table of contents
<!-- TOC -->

- [NEORV32 Serial Runner](#neorv32-serial-runner)
    - [Table of contents](#table-of-contents)
    - [Features](#features)
    - [Getting started](#getting-started)
        - [Quick install Windows](#quick-install-windows)
        - [Manual install](#manual-install)
    - [Usage](#usage)
        - [Import binary file](#import-binary-file)
        - [Run the script](#run-the-script)
            - [On Windows Recommended](#on-windows-recommended)
                - [A. Interactive Mode](#a-interactive-mode)
                - [B. Direct Mode CLI arguments](#b-direct-mode-cli-arguments)
            - [Manual terminal or Linux](#manual-terminal-or-linux)
        - [Available arguments](#available-arguments)
    - [Future improvements](#future-improvements)

<!-- /TOC -->

## Features

- **Smart Auto-Detection:** Automatically scans and detects the correct UART/Silicon Labs COM port.
- **Dynamic Configuration Banner:** Displays a clean configuration panel at startup with clickable file links.
- **Real-time Transfer Progress:** Shows a beautiful interactive progress bar during the binary file upload.
- **Log Management:** Optional logging feature to record everything transmitted over the serial port into organized log files.
- **Interactive serial communication:** Allow sending characters through the serial port.


## Getting started
### Quick install (Windows)
If you are on Windows, you can set up the complete Python environment automatically without effort. 
Simply double-click or run the installer script ([setup.bat](setup.bat)):
```bash
setup.bat
```
It will:
- Check that Python is installed (if not installed, you will have to install it)
- Create and activate the Python virtual environment
- Upgrade pip
- Install needed Python packages


### Manual install
1. Create Python virtual environment
    ```bash
    python -m venv .venv
    ```

2. Activate the virtual environment
    ```bash
    ./.venv/Scripts/activate   # on Windows
    source .venv/bin/activate  # on Linux
    ```

3. Install the required packages
    ```bash
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```


## Usage
### 1. Import binary file
You need to copy your compiled `neorv32_exe.bin` file into the repository's root directory.

### 2. Run the script
#### On Windows (Recommended)
Use the included [run.bat](run.bat) script. It automatically handles the virtual environment activation for you and offers two ways to launch the application:

##### A. Interactive Mode
If you double-click the file `run.bat` or run it without arguments, it will open an interactive setup menu directly inside your terminal. It will ask you with a prompt to validate every available configuration.

##### B. Direct Mode (CLI arguments)
If you pass any arguments, the script will bypass the questions and launch the application immediately with your custom configuration.
```bash
# Launch with default settings (Interactive mode)
run.bat

# Bypass menu: Force logs reflection and local saving directly
run.bat --show-logs --save-logs

# Bypass menu: Force a specific COM port bypassing the auto-detection
run.bat -p COM6
```

#### Manual terminal (or Linux)
Make sure your virtual environment is active, then execute the Python script directly:
```bash
python main.py
python main.py --show-logs --save-logs
python main.py -p /dev/ttyUSB0
```

### Available arguments
- `--show-logs`: Mirrors everything transmitted on the serial port directly inside your current terminal.
- `--save-logs`: Creates a `.txt` file inside a `log` directory and saves the entire session output.
- `-p PORT`, `--port PORT`: Manually forces the application to use a specific serial port interface.

## Future improvements
- Graphical User Interface (`--gui` argument) containing configuration fields and file pickers.
- Configuration saving/loading mechanisms (`--save-config` and `--use--config` JSON arguments)

