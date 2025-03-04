# SSH Login Monitor with Notifications

This script monitors SSH connection attempts (both successful and failed) from `/var/log/auth.log` and sends notifications via [ntfy](https://ntfy.sh/) or any other notification service. You can specify which types of connection attempts to monitor and receive notifications for.

## Features

- Monitors SSH logs (`/var/log/auth.log` by default).
- Sends notifications for:
  - **Successful SSH logins** (High priority).
  - **Failed SSH logins** (Low priority).
  - **SSH disconnections** (Normal priority).
- Optionally sends a notification only for certain types of events, configurable via environment variables.
- Prevents duplicate notifications for the same event.
- Supports dynamic notification headers and token handling.
- Can be run continuously in the background, monitoring new log entries.

## Requirements

- Python 3.x
- `requests` library (for sending notifications)
- `python-dotenv` library (for environment variable management)

## Installation

1. Clone the repository or download the script.

    ```bash
    git clone https://github.com/kinouzero/monitor-ssh.git
    cd monitor-ssh
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project directory. The file should contain the following environment variables:

    ```env
    NTFY_URL=https://ntfy.sh/topic         # URL of the notification service (default: https://ntfy.sh/topic)
    NTFY_TOKEN=your_token_here            # Optional: Authentication token for the notification service
    MONITOR_EVENTS=all                    # Comma-separated list of events to monitor (choices: accepted, failed, disconnected, all)
    SSH_LOG_FILE=your/log/path            # Optional: Path to your log (default: /var/log/auth.log)
    ```

    You can customize the `MONITOR_EVENTS` variable to choose which events to monitor:
    - `accepted` - Successful logins (default for "all")
    - `failed` - Failed logins (default for "all")
    - `disconnected` - Disconnections (default for "all")
    - `all` - Monitors all types of events (default)

4. Run the script:

    ```bash
    python main.py
    ```

## 🚀 Running with Docker

You can run this SSH monitor inside a Docker container.

### 🐳 Build the Docker image

```sh
docker build -t ssh-monitor .
```

### 📦 Run the container

```sh
docker run -d \
  --name ssh-monitor \
  --env NTFY_URL="https://ntfy.sh/topic" \
  --env MONITOR_EVENTS="all" \
  -v /var/log:/app/log \
  ssh-monitor
```

This will run the monitor in the background, using environment variables to configure notifications.

## 📋 Using Docker Compose

If you prefer `docker-compose`, create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  ssh-monitor:
    image: ssh-monitor
    build: .
    restart: unless-stopped
    environment:
      - NTFY_URL=https://ntfy.sh/topic
      - MONITOR_EVENTS=all
    volumes:
      - /var/log:/app/log
```

### ▶ Start the service

```sh
docker-compose up -d
```

### ⏹ Stop the service

```sh
docker-compose down
```

This setup ensures the container restarts automatically and keeps logs accessible.

### Optional: Run as a service

You can configure the script to run as a service using `systemd` (on Linux systems):

1. Create a `monitor-ssh.service` file in `/etc/systemd/system/` with the following content:

    ```ini
    [Unit]
    Description=SSH Connection Monitor
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /path/to/monitor-ssh.py
    WorkingDirectory=/path/to/your/script
    Restart=always
    User=your-user
    Group=your-group

    [Install]
    WantedBy=multi-user.target
    ```

2. Reload `systemd` and start the service:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable monitor-ssh.service
    sudo systemctl start monitor-ssh.service
    ```

## Configuration

The following environment variables can be configured in the `.env` file:

- **NTFY_URL**: The notification URL (default: `https://ntfy.sh/topic`).
- **NTFY_TOKEN**: The optional authentication token for the notification service.
- **MONITOR_EVENTS**: Comma-separated list of events to monitor (`accepted`, `failed`, `disconnected`, `all`). Default is `all`.
- **SSH_LOG_FILE**: Path to your log file (default script: `/var/log/auth.log`, default docker: `/app/log/auth.log`).

### Example `.env` file

```env
NTFY_URL=https://ntfy.sh/topic
NTFY_TOKEN=your_token_here
MONITOR_EVENTS=accepted,failed
SSH_LOG_FILE=your/log/path
```

## Logging

The script logs its activities to `/tmp/monitor-ssh.log` by default.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
