#!/usr/bin/env python3

import re
import requests
import logging
import os
import sys
import signal
import subprocess
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Configuration
LOG_OUTPUT = "/tmp/monitor-ssh.log"
LOCK_FILE = "/tmp/monitor-ssh.lock"
SSH_LOG_FILE = "/var/log/auth.log"
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh/topic")
NTFY_TOKEN = os.getenv("NTFY_TOKEN")
MONITOR_EVENTS = os.getenv("MONITOR_EVENTS", "all").split(",")

# Check if another instance is already running
if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "r") as f:
        old_pid = f.read().strip()
    if old_pid and os.path.exists(f"/proc/{old_pid}"):
        print(f"⚠️ The script is already running under the PID {old_pid}.")
        sys.exit(1)

# Write the current PID to the lock file
with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))

# Remove the lock file on exit
def cleanup(signum=None, frame=None):
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

# Logging configuration
logging.basicConfig(filename=LOG_OUTPUT, level=logging.INFO, format="%(asctime)s - %(message)s")

# Event history to prevent duplicate notifications
event_cache = set()

# Send a notification
def send_notification(event_type, user, client_ip, priority, raw_log):
    message = (
        f"🔑 {event_type}\n\n"
        f"👤 User: {user}\n"
        f"🌍 IP: {client_ip}\n"
    )

    # Check if this event has already been processed
    event_id = f"{event_type}-{user}-{client_ip}"
    if event_id in event_cache:
        return
    event_cache.add(event_id)

    # Dynamically build headers (without token if not defined)
    headers = {"Priority": priority}
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"

    try:
        response = requests.post(
            NTFY_URL,
            headers=headers,
            data=message.encode("utf-8"),
            timeout=5
        )
        if response.status_code != 200:
            logging.error(f"Failed to send notification (HTTP {response.status_code}): {response.text}")
        else:
            logging.info(f"Notification sent: {message}")
    except requests.RequestException as e:
        logging.error(f"Error sending notification: {e}")

# Analyze a log line
def parse_log_line(line):
    # Successful connection (HIGH PRIORITY)
    if "accepted" in MONITOR_EVENTS or "all" in MONITOR_EVENTS:
        match = re.search(r"sshd\[\d+\]: Accepted \w+ for (\S+) from (\S+)", line)
        if match:
            user, client_ip = match.groups()
            send_notification("Successful SSH login", user, client_ip, "high", line)
            return

    # Failed connection (LOW PRIORITY)
    if "failed" in MONITOR_EVENTS or "all" in MONITOR_EVENTS:
        match = re.search(r"sshd\[\d+\]: Failed \w+ for (\S+) from (\S+)", line)
        if match:
            user, client_ip = match.groups()
            send_notification("Failed SSH login", user, client_ip, "min", line)
            return

    # Disconnection (NORMAL PRIORITY)
    if "disconnected" in MONITOR_EVENTS or "all" in MONITOR_EVENTS:
        match = re.search(r"sshd\[\d+\]: Disconnected from authenticating user (\S+) (\S+)", line)
        if match:
            user, client_ip = match.groups()
            send_notification("SSH disconnection", user, client_ip, "default", line)
            return

# Main function: monitor the log file using tail -f
def monitor_auth_log():
    with subprocess.Popen(['tail', '-f', SSH_LOG_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as proc:
      try:
          for line in iter(proc.stdout.readline, ''):
              if "sshd" in line:
                  parse_log_line(line)
      except Exception as e:
          logging.error(f"Erreur lors de la lecture du fichier : {e}")
      finally:
          proc.terminate()
          proc.wait()


if __name__ == "__main__":
    try:
        monitor_auth_log()
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        cleanup()
