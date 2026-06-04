import os
from io import TextIOWrapper
from serial import Serial
import time
from datetime import datetime
import argparse
from colorama import Fore, Style, init
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

init(autoreset=True) # colorama: reset after each print()

class Config:
    COM_PORT: str = 'COM6'
    BAUDRATE: int = 19200
    BIN_FILE: str = 'neorv32_exe.bin'
    LOG_DIR: str = "log"


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


def print_banner(save_logs: bool, show_logs: bool, log_file: TextIOWrapper | None):
    bin_folder_path = os.path.dirname(os.path.abspath(Config.BIN_FILE))
    log_folder_path = os.path.abspath(Config.LOG_DIR)
    if save_logs and log_file:
        log_file_path = os.path.abspath(log_file.name)
        log_file_name = os.path.basename(log_file_path) if log_file_path else "N/A"
        log_file_link = f" ([cyan][link=file:///{log_file_path}]{log_file_name}[/link][/cyan])" if save_logs and log_file else ""
    else:
        log_file_link = ""
    
    log_status = "[green]Enabled[/green]" if save_logs else "[dim]Disabled[/dim]"
    show_status = "[green]Enabled[/green]" if show_logs else "[dim]Disabled[/dim]"
    
    banner_text = f"""[bold]OPTIONS AVAILABLE[/bold]
    --save-logs: create a .txt log file and store everything that is transmitted on the serial port
    --show-logs: show everything that is transmitted on the serial port in the current terminal
    
[bold]CONFIG[/bold]
    • Port      : {Config.COM_PORT} ({Config.BAUDRATE} baud)
    • Binary    : [link=file:///{bin_folder_path}]{Config.BIN_FILE}[/link]
    • Log Dir   : [link=file:///{log_folder_path}]{Config.LOG_DIR}[/link]
    • Save logs : {log_status}{log_file_link}
    • Show logs : {show_status}"""
    
    rprint(Panel(banner_text,
                 title="[bold]NEORV32 Serial Runner[/bold]",
                 title_align="center",
                 border_style="cyan"))


def open_serial_port() -> Serial:
    ret = None
    print(f"\nOpening port {Style.BRIGHT}{Config.COM_PORT}{Style.NORMAL}...", end="")
    
    try:
        # Open port with a timeout
        ser = Serial(Config.COM_PORT, Config.BAUDRATE, timeout=3)
        print_ok()
        ret = ser
    except Exception as e:
        print_ko()
        print_error(f"Error opening port: {e}")
    
    return ret


def wait_for_bootloader(ser, history: list[str]):
    print("Waiting for bootloader (use reset switch on the board)...", end="")
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
    file_size = os.path.getsize(Config.BIN_FILE)
    rprint(f"Sending binary file [cyan]{Config.BIN_FILE}[/cyan] ({format_size(file_size)})")
    
    try:
        with Progress(TextColumn("  "),
                      BarColumn(bar_width=30),
                      DownloadColumn(),
                      TransferSpeedColumn(),
                      TimeRemainingColumn()) as progress:
            task = progress.add_task("", total=file_size)
            
            with open(Config.BIN_FILE, 'rb') as f:
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
        print_error(f"Error: {Config.BIN_FILE} not found.")

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
    if not os.path.exists(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR)
    
    # Log file name, format: YYYYMMDDhhmmss_logs.txt
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S_logs.txt")
    filename = os.path.join(Config.LOG_DIR, timestamp)
    
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
    finally:
        if log_file:
            log_file.close()


def upload_and_run(save_logs, show_logs, log_file):
    ser = open_serial_port()
    if ser is None:
        return
    
    # List that contains everything that is transmitted on the port since the boot
    boot_history = []

    try:
        wait_for_bootloader(ser, boot_history)
        if not abort_autoboot(ser, boot_history): return
        if not send_upload_command(ser): return
        if not send_binary_file(ser): return
        if not send_execute_command(ser): return
        
        handle_logs(ser, log_file, save_logs, show_logs, boot_history)
    
    except KeyboardInterrupt:
        print("\n\nEnd of script.")
    finally:
        ser.close()

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="NEORV32 Serial Runner")
    parser.add_argument("--save-logs", action="store_true", help="Save the output logs into a file")
    parser.add_argument("--show-logs", action="store_true", help="Display the output logs in the terminal")
    args = parser.parse_args()
    
    # Clear terminal
    Console().clear()    
    
    # Create log if needed
    log_file = None
    if args.save_logs:
        log_file = create_log_file()
    
    # Main program
    print_banner(save_logs=args.save_logs, show_logs=args.show_logs, log_file=log_file)
    upload_and_run(save_logs=args.save_logs, show_logs=args.show_logs, log_file=log_file)
    
    print()
