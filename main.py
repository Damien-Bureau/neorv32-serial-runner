import os
from io import TextIOWrapper
from serial import Serial, SerialException
from serial.tools import list_ports
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
    COM_PORT: str | None = None # detected automatically or set by user
    BAUDRATE: int = 19200
    BIN_FILE: str = 'neorv32_exe.bin'
    LOG_DIR: str = "log"


def print_ok():
    print(Fore.GREEN + "OK")
    
def print_ko():
    print(Fore.RED + "KO")
    
def print_error(msg):
    rprint(f"[red]{msg}[/red]")
    
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
    --save-logs     : create a .txt log file and store everything that is transmitted on the serial port
    --show-logs     : show everything that is transmitted on the serial port in the current terminal
    --port, -p PORT : force a specific COM port (e.g., COM6 or /dev/ttyUSB0)
    
[bold]CONFIG[/bold]
    • Port      : [green]{Config.COM_PORT}[/green] ({Config.BAUDRATE} baud)
    • Binary    : [cyan][link=file:///{bin_folder_path}]{Config.BIN_FILE}[/link][/cyan]
    • Log Dir   : [cyan][link=file:///{log_folder_path}]{Config.LOG_DIR}[/link][/cyan]
    • Save logs : {log_status}{log_file_link}
    • Show logs : {show_status}"""
    
    rprint(Panel(banner_text,
                 title="[bold]NEORV32 Serial Runner[/bold]",
                 title_align="center",
                 border_style="cyan"))


def check_port(port) -> bool:
    available_ports = [p.device for p in list_ports.comports()]
    
    # Check if port exists
    if port not in available_ports:
        print_error(f"Port '[bold]{port}[/bold]' does not exist.")
        print(f"Available ports: {', '.join(available_ports) if available_ports else 'None'}\n")
        return False
    
    # Try accessing port
    try:
        test_ser = Serial(port)
        test_ser.close()
        return True
    except:
        print_error(f"Port '[bold]{port}[/bold]' is already in use by another application.")
        return False


def auto_detect_port() -> str | None:
    start_time = time.time()
    timeout = start_time + 5
    
    last_seconds_left = -1
    while time.time() < timeout:
        seconds_left = int(timeout - time.time() + 0.9)
        if seconds_left != last_seconds_left and seconds_left > 0:
            print(f"\rDetecting serial port...{Style.DIM}{seconds_left}s{Style.NORMAL}", end="", flush=True)
            last_seconds_left = seconds_left
        
        ports = list(list_ports.comports())
        
        if ports:
            for port in ports:
                desc = port.description.lower()
                if "silicon labs" in desc or "uart" in desc:
                    print(f"\rDetecting serial port...", end="", flush=True)
                    return port.device
        
        time.sleep(0.1)
    
    print(f"\rDetecting serial port...", end="", flush=True)
    return None


def handle_no_port():
    print_error("\nNo serial port detected.")
    print("Please check your connections or enter manually the port using the --port argument.\n")
    exit(1)


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
    except SerialException as e:
        print_error(f"\n\n{e}")
    finally:
        ser.close()


if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="NEORV32 Serial Runner")
    parser.add_argument("--save-logs", action="store_true", help="Save the output logs into a file")
    parser.add_argument("--show-logs", action="store_true", help="Display the output logs in the terminal")
    parser.add_argument("-p", "--port", type=str, help="Force a specific COM port (e.g., COM6 or /dev/ttyUSB0)")
    args = parser.parse_args()
    
    # Clear terminal
    Console().clear()
        
    # Auto detect com port
    if args.port:
        if check_port(args.port):
            Config.COM_PORT = args.port
        else:
            exit(1)
    else:
        port = auto_detect_port()
        if port:
            print_ok()
            time.sleep(0.2)
            Console().clear()
            Config.COM_PORT = port
        else:
            print_ko()
            Config.COM_PORT = "[red]NONE[/red]"
            handle_no_port()
    
    # Create log file if needed
    log_file = None
    if args.save_logs:
        log_file = create_log_file()
    
    # Main program
    print_banner(save_logs=args.save_logs, show_logs=args.show_logs, log_file=log_file)
    upload_and_run(save_logs=args.save_logs, show_logs=args.show_logs, log_file=log_file)
    
    print()
