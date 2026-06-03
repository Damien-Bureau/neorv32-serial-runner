import os
import serial
import time
from datetime import datetime
import argparse
from colorama import Fore, Style, init

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

def upload_and_run(save_logs, show_logs):
    print(f"\nOpening port {Style.BRIGHT}{PORT_COM}{Style.NORMAL}...", end="")
    try:
        # Open port with a timeout
        ser = serial.Serial(PORT_COM, BAUDRATE, timeout=3)
        print_ok()
    except Exception as e:
        print_ko()
        print_error(f"Error opening port: {e}")
        return

    print("Waiting for RESET (switch on the board)...", end="")
    
    bootloader_detected = False
    
    # Wait for a message from the bootloader
    while not bootloader_detected:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore')
            
            # Bootloader usually shows "NEORV32"
            if "NEORV32" in line or "Bootloader" in line or "CMD" in line:
                print_ok()
                bootloader_detected = True

    # Send a key to stop auto boot
    print("Stopping automatic boot...", end="")
    ser.reset_input_buffer()
    ser.write(b'\n') 
    abort_confirmed = False
    buffer = ""
    timeout_abort = time.time() + 2.0
    while not abort_confirmed and time.time() < timeout_abort:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            buffer += chunk
            
            if "Aborted." in buffer:
                abort_confirmed = True
    # time.sleep(0.2) # let the bootloader process
    if abort_confirmed:
        print_ok()
    else:
        print_ko()
        print_error("\nError: Bootloader did not confirm the abort")
        ser.close()
        return
    
    # Send 'u' to start upload
    print("Sending upload command ('u')...", end="")
    ser.write(b'u')
    time.sleep(0.5)
    print_ok()
    
    # Send binary file
    print(f"Sending file {Fore.CYAN}{BIN_FILE}{Fore.RESET}...", end="")
    try:
        with open(BIN_FILE, 'rb') as f:
            bin_content = f.read()
            
        ser.write(bin_content)
        ser.flush()
        print_ok()
    except FileNotFoundError:
        print_ko()
        print_error(f"Error: {BIN_FILE} not found.")
        ser.close()
        return

    time.sleep(0.5)
    
    # Send 'e' to execute
    print("Sending execute command ('e')...", end="")
    ser.write(b'e')
    print_ok()
    
    # Logs management
    if save_logs:
        # Create log folder if it doesn't exist
        if not os.path.exists(LOG_FOLDER):
            os.makedirs(LOG_FOLDER)
        
        # Log file name, format: YYYYMMDDhhmmss_logs.txt
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S_logs.txt")
        filename = os.path.join(LOG_FOLDER, timestamp)
        print(f"Creating log file {Fore.CYAN}{filename}{Fore.RESET}...", end="")
        
        # Open log file
        log_file = open(filename, "w", encoding="utf-8", newline="")
        print_ok()
        
        print("Listening to logs (Press Ctrl+C to stop)...")
    else:
        print("\nPress Ctrl+C to stop")
    
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
        ser.close()

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="NEORV32 Flasher and Logger")
    parser.add_argument("--save-logs", action="store_true", help="Save the output logs into a file")
    parser.add_argument("--show-logs", action="store_true", help="Display the output logs in the terminal")
    args = parser.parse_args()
    
    # Call main function with parsed options
    upload_and_run(save_logs=args.save_logs, show_logs=args.show_logs)
