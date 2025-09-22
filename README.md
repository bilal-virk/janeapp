# Welcome to Janeapp
This janeapp script contains two parts seleniumbase for automation and FastAPI for managing API access. User can check NordVPN status, connnect to VPN by entering city or country name, GET or POST call to automation script  to start automation.
## How Automation Script is Working
To start automation script user need to provide web portal url, username  and password for [https://eddinscounseling.janeapp.com/admin](https://eddinscounseling.janeapp.com/admin). After recieving automation call script will first varify if nordvpn connected or not. If not connected it will reject call and instruct user to first connect to VPN.
If VPN is connected it will start automation script using seleniumgrid on port 4444.
It will  start a headless chrome session and login to janeapp and then  it  will open each url one by one set starting and ending date and download report file. All the downloaded report files will be copied to "downloaded_files" folder.
Once all the urls are processed it will upload all the csv files to Supabase database using API endpoint [https://mmayynuyhfvbcgofgnma.storage.supabase.co/storage/v1/s3](https://mmayynuyhfvbcgofgnma.storage.supabase.co/storage/v1/s3) it will create a bucket with URL + Username and upload files to this bucket (folder).
After uploading all the files it will delete all the local csv files.

  

## API Endpoints

  

### 1. Get VPN Status

**Endpoint:**

```

GET /vpn-status/

```

  

**Description:**

Returns the current NordVPN connection status (connected/disconnected, server, country, etc.).

  

**Response Example:**

```json

{

"connected": true,

"country": "United States",

"city": "New York",

"ip": "178.156.205.76"

}

```

  

---

  

### 2. Connect to VPN

**Endpoint:**

```

POST /connect-vpn/?country={country_or_city}

```

  

**Description:**

Connects to NordVPN in the specified country or city.

If already connected, the API disconnects first before reconnecting.

  

**Query Parameters:**

-  `country`  *(string, optional, default: "us")* → Country or city name to connect.

  

**Example Requests:**

```

POST /connect-vpn/?country=us

POST /connect-vpn/?country=berlin

```

  

**Response Example:**

```json

{

"stdout": "Connecting to United States #134...",

"stderr": "",

"returncode": 0,

"status": {

"connected": true,

"country": "United States",

"city": "New York",

"ip": "178.156.205.76"

}

}

```

  

---

  

### 3. Run Automation Script

**Endpoint:**

```

GET /run-script

POST /run-script

```

  

**Description:**

Starts a SeleniumBase automation script on the Selenium Grid.

Requires **NordVPN to be connected**.

  

**Query Parameters (required):**

-  `username`  *(string)* → JaneApp username.

-  `password`  *(string)* → JaneApp password.

-  `url`  *(string)* → Target URL (must contain `janeapp.com`).

  

**Example Request:**

```

POST /run-script?username=user@example.com&password=securePass123&url=https://eddinscounseling.janeapp.com/admin

```

  

**Response Example:**

```json

{

"message": "SeleniumBase script started on Grid in background.",

"current_sessions": 2,

"vpn_status": {

"connected": true,

"country": "Germany",

"city": "Berlin",

"ip": "178.156.205.99"

}

}

```

  

**Error Responses:**

- VPN not connected:

```json

{

"error": "VPN not connected. Please connect first.",

"status": { "connected": false }

}

```

- Invalid URL:

```json

{

"error": "❌ URL https://example.com not allowed",

"vpn_status": { "connected": true }

}

```

  

---

  

### 4. Get Logs

**Endpoint:**

```

GET /logs/?log_lines={n}

```

  

**Description:**

Fetches the last `n` lines from the application log file.

  

**Query Parameters:**

-  `log_lines`  *(integer, optional, default: 200)* → Number of log lines to return.

  

**Example Request:**

```

GET /logs/?log_lines=100

```

  

**Response Example:**

```json

{

"log_lines_returned": 100,

"logs": "2025-09-21 12:30:05 INFO: Connected to VPN\n2025-09-21 12:31:07 INFO: Script started..."

}

```

  

---

# ⚙️ Installation Guide (VPS Setup)

  

This guide explains how to set up the environment on your VPS, install dependencies, configure **NordVPN**, whitelist ports, set up **Selenium Grid**, and run the FastAPI service with **Uvicorn**.

  

---

  

## 1. Install System Packages

Update and install required dependencies:

```bash

sudo  apt  update && sudo  apt  upgrade  -y

sudo  apt  install  -y  python3  python3-venv  python3-pip  curl  wget  unzip  git  docker.io  docker-compose

```

  

---

  

## 2. Create Python Virtual Environment

```bash

# Create virtual environment

python3  -m  venv  venv

  

# Activate virtual environment

source  venv/bin/activate

```

  

---

  

## 3. Install Required Python Libraries

Inside the virtual environment, install required dependencies:

```bash

pip  install  --upgrade  pip

pip  install  fastapi  uvicorn  seleniumbase  boto3  botocore  psutil

```

  

---

  

## 4. Install NordVPN on VPS

```bash

sh  <(curl  -sSf https://downloads.nordcdn.com/apps/linux/install.sh)

```

  

Check version:

```bash

nordvpn  --version

```

  

---

  

## 5. Login to NordVPN Using Access Token

```bash

nordvpn  login  --token  {access_token}

```

Replace `{access_token}` with your token from the NordVPN dashboard.

  

---

  

## 6. Whitelist Ports for VPS Access

You need to whitelist port 22 and port  for nordvpn it will make sure you can still access your VPS (SSH) and FastAPI endpoints while using NordVPN.

  

```bash

# Allow SSH (port 22)

nordvpn  whitelist  add  port  22

  

# Allow FastAPI (port 8000)

nordvpn  whitelist  add  port  8000

```

  

---

  

## 7. Setup Selenium Grid with Docker

Create and start a Selenium Grid using Docker.

  

```bash

# Start Selenium Grid Hub

docker  run  -d  -p  4442-4444:4442-4444  --name  selenium-hub  selenium/hub:latest

  

# Start Chrome Node

docker  run  -d  --name  selenium-node-chrome  --link  selenium-hub:hub  -p  7900:7900  selenium/node-chrome:4.21.0

 
```

  

Check Selenium Grid status:

```

http://<your_vps_ip>:4444/ui

```

  

---

  

## 8. Start FastAPI with Uvicorn

Run the FastAPI app (`app.py`) using Uvicorn on port **8000**:

  

```bash

# Inside virtual environment

uvicorn  app:app  --host  0.0.0.0  --port  8000  --reload

```

  

This will serve your API at:

```

http://<your_vps_ip>:8000

```

  


  

---

  

#### You now have:

- NordVPN installed & whitelisted

- FastAPI running on port **8000**

- Selenium Grid running in Docker
