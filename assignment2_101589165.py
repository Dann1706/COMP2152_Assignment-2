"""
Author: Daniel Alvarez
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket
import threading
import sqlite3
import os
import platform
import datetime

# TODO: Print Python version and OS name (Step iii)

print("Python Version:", platform.python_version())
print("Operating System:", os.name)


# TODO: Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}


# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"
class NetworkTool:
    def __init__(self, target):
        self.__target = target  # private property

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value != "":
            self.__target = value
        else:
            print("Error: Target cannot be empty")

    def __del__(self):
        print("NetworkTool instance destroyed")


# Q3: What is the benefit of using @property and @target.setter?
# TODO: Your 2-4 sentence answer here... (Part 2, Q3)
# using it gives you controlled access to a private attribute, enabling safe reading of its value
# it target.setter lets us add validation logic like preventing the target form being set to
# an empty string. 


# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)
# the PortScanner inherits from networktool so it can reuse
# the target property and the getters and setters

# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

# - scan_port(self, port):
#     Q4: What would happen without try-except here?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q4)
#     without it, any network related error would cause the program to crash
#     so it is essential to have it to ensure errors are caught and handled
#
#     - try-except with socket operations
#     - Create socket, set timeout, connect_ex
#     - Determine Open/Closed status
#     - Look up service name from common_ports (use "Unknown" if not found)
#     - Acquire lock, append (port, status, service_name) tuple, release lock
#     - Close socket in finally block
#     - Catch socket.error, print error message
#
    def scan_port(self, port):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            status = "Open" if result == 0 else "Closed"
            service_name = common_ports.get(port, "Unknown")
            with self.lock:
                self.scan_results.append((port, status, service_name))
        except socket.error as e:
            print(f"Error scanning port {port}: {e}")
        finally:
            if sock:
                sock.close()

# - get_open_ports(self):
# - Use list comprehension to return only "Open" results
#
    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

#     Q2: Why do we use threading instead of scanning one port at a time?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q2)
#     because it allowws the program to scan multiple ports at the same time and helps reduce
#     the total scan time. It also allos the scanner to handle slow or unresponsive ports without
#     blocking the rest of tthe scan
#
# - scan_range(self, start_port, end_port):
#     - Create threads list
#     - Create Thread for each port targeting scan_port
#     - Start all threads (one loop)
#     - Join all threads (separate loop)
    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()


# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
def save_results(target, results):
    """
    Saves port scan results to an SQLite database (scan_history.db)
    """
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT
            )
        """)
        for port, status, service in results:
            cursor.execute("""
                INSERT INTO scans (target, port, status, service, scan_date)
                VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, datetime.datetime.now()))
        conn.commit()
        conn.close()
        print(f"Results saved for target {target}.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection
def load_past_scans():
    """
    Loads and prints all past scans from scan_history.db in a readable format.
    """
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()
        if rows:
            print("\nPast Scan History:")
            for row in rows:
                scan_id, target, port, status, service, scan_date = row
                print(f"ID: {scan_id}, Target: {target}, Port: {port}, Status: {status}, Service: {service}, Date: {scan_date}")
        else:
            print("No past scans found.")
        conn.close()
    except sqlite3.Error:
        print("No past scans found.")


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
      # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    target = input("Enter target IP (default 127.0.0.1): ").strip()
    if not target:
        target = "127.0.0.1"

    # Get start and end ports with validation
    while True:
        try:
            start_port = int(input("Enter start port (1-1024): "))
            end_port = int(input("Enter end port (1-1024): "))
            
            if not (1 <= start_port <= 1024) or not (1 <= end_port <= 1024):
                print("Port must be between 1 and 1024.")
                continue
            if end_port < start_port:
                print("End port must be greater than or equal to start port.")
                continue
            break  # valid input, exit loop
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    print(f"Scanning {target} from port {start_port} to {end_port}...")
    pass


    # TODO: After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()target = input("Enter target IP (default 127.0.0.1): ").strip()

    # Create PortScanner object
    scanner = PortScanner(target)
    print(f"\nScanning {target} from port {start_port} to {end_port}...\n")

    # Scan ports
    scanner.scan_range(start_port, end_port)

    # Get open ports
    open_ports = scanner.get_open_ports()

    # Print scan results
    print(f"--- Scan Results for {target} ---")
    for port, status, service in open_ports:
        print(f"Port {port}: {status} ({service})")
    print("------")
    print(f"Total open ports found: {len(open_ports)}\n")

    # Save results to database
    save_results(target, scanner.scan_results)

    # Ask if user wants to see past scans
    view_history = input("Would you like to see past scan history? (yes/no): ").strip().lower()
    if view_history == "yes":
        load_past_scans()

# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)
# a new feature could be like a port scan scheduling option that allows the user to 
# schedule scans at specific times or intervals

# Diagram: See diagram_studentID.png in the repository root
