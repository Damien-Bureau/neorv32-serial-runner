import serial
import time
from colorama import Fore, Style, init

init(autoreset=True) # colorama: reset after each print()

# --- CONFIGURATION ---
PORT_COM = 'COM6'
BAUDRATE = 19200
BIN_FILE = 'neorv32_exe.bin'

def print_ok():
    print(Fore.GREEN + "OK")
    
def print_ko():
    print(Fore.RED + "KO")

def upload_and_run():
    print(f"\nOpening port {Style.BRIGHT}{PORT_COM}{Style.NORMAL}...", end="")
    try:
        # Open port with a timeout
        ser = serial.Serial(PORT_COM, BAUDRATE, timeout=3)
        print_ok()
    except Exception as e:
        print_ko()
        print(f"Error opening port: {e}")
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
    ser.write(b'\n') 
    time.sleep(0.2) # let the bootloader process
    print_ok()
    
    # Send 'u' to start upload
    print("Sending upload command ('u')...", end="")
    ser.write(b'u')
    time.sleep(0.5)
    print_ok()
    
    # Send binary file
    print(f"Sending file {BIN_FILE}...", end="")
    try:
        with open(BIN_FILE, 'rb') as f:
            bin_content = f.read()
            
        ser.write(bin_content)
        ser.flush()
        print_ok()
    except FileNotFoundError:
        print_ko()
        print(f"Error: {BIN_FILE} not found.")
        ser.close()
        return

    time.sleep(0.5)
    
    # Send 'e' to execute
    print("Sending execute command ('e')...", end="")
    ser.write(b'e')
    print_ok()
    
    # Optional: show program logs
    print("\n--- Program logs ---")
    try:
        while True:
            if ser.in_waiting > 0:
                print(ser.read(ser.in_waiting).decode('utf-8', errors='ignore'), end='')
    except KeyboardInterrupt:
        print("\nEnd of script.")
    finally:
        ser.close()

if __name__ == "__main__":
    upload_and_run()