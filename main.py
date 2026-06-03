import os
import serial
from serial import Serial
import time
from datetime import datetime
import argparse
from colorama import Fore, Style, init
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich import print as rprint

init(autoreset=True) # colorama: reset after each print()

# --- CONFIGURATION ---
PORT_COM = 'COM6'
BAUDRATE = 19200
BIN_FILE = 'neorv32_exe.bin'
LOG_FOLDER = "log"

def print_ok():
    print(Fore.GREEN + "OK")
    
def print_ko():
    print(Fore.RED + "KO")
    
def print_error(msg):
    print(Fore.RED + msg)
    
def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024: 
        return f"{size_bytes/1024:.1f} kB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"


def open_serial_port() -> Serial:
    ret = None
    print(f"\nOpening port {Style.BRIGHT}{PORT_COM}{Style.NORMAL}...", end="")
    
    try:
        # Open port with a timeout
        ser = serial.Serial(PORT_COM, BAUDRATE, timeout=3)
        print_ok()
        ret = ser
    except Exception as e:
        print_ko()
        print_error(f"Error opening port: {e}")
    
    return ret


def wait_for_bootloader(ser, history: list[str]):
    print("Waiting for RESET (switch on the board)...", end="")
    bootloader_detected = False
    buffer = ""
    
    # Wait for a message from the bootloader
    while not bootloader_detected:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            buffer += chunk
            history.append(chunk)
            
            # Bootloader usually shows "NEORV32"
            if "NEORV32" in buffer:
                print_ok()
                bootloader_detected = True


def abort_autoboot(ser, history: list[str]) -> bool:
    ret = False
    print("Aborting automatic boot...", end="")
    
    ser.write(b'\n') 
    abort_confirmed = False
    buffer = ""
    timeout_abort = time.time() + 2.0
    while not abort_confirmed and time.time() < timeout_abort:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            buffer += chunk
            history.append(chunk)
            
            if "Aborted." in buffer:
                abort_confirmed = True
    if abort_confirmed:
        print_ok()
        ret = True
    else:
        print_ko()
        print_error("\nError: Bootloader did not confirm the abort")
    
    return ret


def send_upload_command(ser) -> bool:
    ret = False
    print("Sending upload command ('u')...", end="")
    
    ser.write(b'u')
    time.sleep(0.5)
    print_ok()
    
    ret = True
    return ret


def send_binary_file(ser) -> bool:
    ret = False
    file_size = os.path.getsize(BIN_FILE)
    rprint(f"Sending file [cyan]{BIN_FILE}[/cyan] ({format_size(file_size)})")
    
    try:
        with Progress(TextColumn("  "),
                      BarColumn(bar_width=30),
                      DownloadColumn(),
                      TransferSpeedColumn(),
                      TimeRemainingColumn()) as progress:
            task = progress.add_task("", total=file_size)
            
            with open(BIN_FILE, 'rb') as f:
                chunk_size = 512
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    ser.write(chunk)
                    ser.flush()
                    progress.update(task, advance=len(chunk))
        ret = True
    except FileNotFoundError:
        print_ko()
        print_error(f"Error: {BIN_FILE} not found.")

    return ret


def send_execute_command(ser) -> bool:
    ret = False
    print("Sending execute command ('e')...", end="")
    
    ser.write(b'e')
    print_ok()
    
    ret = True
    return ret


def create_log_file():
    # Create log folder if it doesn't exist
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
    
    # Log file name, format: YYYYMMDDhhmmss_logs.txt
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S_logs.txt")
    filename = os.path.join(LOG_FOLDER, timestamp)
    abs_path = os.path.abspath(filename)
    rprint(f"Creating log file [cyan][link=file:///{abs_path}]{filename}[/link][/cyan]...", end="")
    
    # Open log file
    log_file = open(filename, "w", encoding="utf-8", newline="")
    print_ok()
    
    return log_file
    

def handle_logs(ser, log_file, save_logs, show_logs, history: list[str]):
    if save_logs:
        print("\nListening to logs (Press Ctrl+C to stop)...")
    else:
        print("\nPress Ctrl+C to stop")
    
    boot_logs = "".join(history)
    if show_logs:
        print(boot_logs, end="")
    if save_logs and log_file:
        log_file.write(boot_logs)
        log_file.flush()
    
    try:
        while True:
            if ser.in_waiting > 0:
                # Read all available data
                serial_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                
                if show_logs:
                    print(serial_data, end="")
                
                if save_logs and log_file:
                    log_file.write(serial_data)
                    log_file.flush()
                    
    except KeyboardInterrupt:
        print("\nEnd of script.")
    finally:
        if log_file:
            log_file.close()


def upload_and_run(save_logs, show_logs):
    ser = open_serial_port()
    if ser is None:
        return
    
    # List that contains everything that is transmitted on the port since the boot
    boot_history = []

    wait_for_bootloader(ser, boot_history)
    
    log_file = None
    if save_logs:
        log_file = create_log_file()

    try:
        if not abort_autoboot(ser, boot_history): return
        if not send_upload_command(ser): return
        if not send_binary_file(ser): return
        if not send_execute_command(ser): return
        
        handle_logs(ser, log_file, save_logs, show_logs, boot_history)
    
    finally:
        ser.close()

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="NEORV32 Flasher and Logger")
    parser.add_argument("--save-logs", action="store_true", help="Save the output logs into a file")
    parser.add_argument("--show-logs", action="store_true", help="Display the output logs in the terminal")
    args = parser.parse_args()
    
    # Call main function with parsed options
    upload_and_run(save_logs=args.save_logs, show_logs=args.show_logs)
