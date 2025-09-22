from fastapi import FastAPI
import subprocess
import requests, os
import psutil
import shutil
from fastapi import Query
import tempfile
import uuid
from threading import Thread
app = FastAPI()
LOG_FILE = "app.log"
def vpn_status():
    result = subprocess.run(["nordvpn", "status"], capture_output=True, text=True)
    connected = "Status: Connected" in result.stdout

    ip_info = {}
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5)
        if res.status_code == 200:
            data = res.json()
            ip_info = {
                "ip": data.get("ip"),
                "city": data.get("city"),
                "region": data.get("region"),
                "country": data.get("country"),
                "org": data.get("org"),
            }
    except Exception as e:
        ip_info = {"error": str(e)}

    return {
        "connected": connected,
        "raw_status": result.stdout.strip(),
        "ip_info": ip_info,
    }

@app.get("/vpn-status/")
async def get_vpn_status():
    return vpn_status()

@app.post("/connect-vpn/")
async def connect_vpn(country: str = "us"):
    # Disconnect first (ignore errors if already disconnected)
    subprocess.run(["nordvpn", "disconnect"], capture_output=True)

    # Connect to new location
    result = subprocess.run(["nordvpn", "connect", country], capture_output=True, text=True)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "status": vpn_status()
    }

# @app.api_route("/run-script/", methods=["GET", "POST"])
# async def run_script(username: str = Query(...), password: str = Query(...), url: str = Query(...)):
#     status = vpn_status()
#     vpn = vpn_status()
#     if not status["connected"]:
#         return {"error": "VPN not connected. Please connect first.", "status": status}
#     if "janeapp.com" not in url:
#         return {"error": f"❌ URL {url} not allowed", "vpn_status": vpn}
#     os.environ["SB_USERNAME"] = username
#     os.environ["SB_PASSWORD"] = password
#     cmd = [
#     "python3", "selb_app.py",
#     "--server=localhost", "--port=4444", "--browser=chrome", "--headless" 
# ]
#     try:
#         result = subprocess.run(cmd, capture_output=True, text=True, check=False)
#         return {
#             "stdout": result.stdout,
#             "stderr": result.stderr,
#             "returncode": result.returncode,
#             "vpn_status": vpn
#         }
#     except Exception as e:
#         return {"error": str(e), "vpn_status": vpn}

def run_selb_script(username, password, server="localhost", port="4444", browser="chrome", headless=True, log_file="app.log"):
    unique_folder = os.path.join(tempfile.gettempdir(), f"selb_run_{uuid.uuid4().hex}")
    os.makedirs(unique_folder, exist_ok=True)
    shutil.copy("selb_app.py", os.path.join(unique_folder, "selb_app.py"))
    env = os.environ.copy()
    env["SB_USERNAME"] = username
    env["SB_PASSWORD"] = password
    cmd = [
        "python3", "selb_app.py",
        f"--server={server}",
        f"--port={port}",
        f"--browser={browser}",
        "--grid"
    ]
    if headless:
        cmd.append("--headless")
        
    with open(log_file, "a") as f_log:
        process = subprocess.Popen(
            cmd,
            cwd=unique_folder,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True,                # Return strings instead of bytes
            bufsize=1                  # Line-buffered
        )

        # Stream output line by line to the log file
        for line in process.stdout:
            f_log.write(line)
            f_log.flush()  # Force write to file immediately

        process.wait()  # Wait for process to finish

    # Clean up temporary folder
    shutil.rmtree(unique_folder, ignore_errors=True)

    return process.returncode
    # process = subprocess.Popen(
    #     cmd,
    #     cwd=unique_folder,         # Run from that folder
    #     env=env,                   # Pass updated environment
    #     stdout=subprocess.PIPE,    # Capture logs if needed
    #     stderr=subprocess.PIPE
    # )
    # stdout, stderr = process.communicate()
    
    
    # shutil.rmtree(unique_folder, ignore_errors=True)
    
    
    # return process.returncode, stdout.decode(), stderr.decode()

def count_running_sessions(script_name="selb_app.py"):
    count = 0
    for proc in psutil.process_iter(["cmdline"]):
        try:
            if proc.info["cmdline"] and script_name in " ".join(proc.info["cmdline"]):
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return count

@app.api_route("/run-script", methods=["GET", "POST"])
async def run_script(
    username: str = Query(...),
    password: str = Query(...),
    url: str = Query(...),
):
    status = vpn_status()
    if not status["connected"]:
        return {"error": "VPN not connected. Please connect first.", "status": status}

    if "janeapp.com" not in url:
        return {"error": f"❌ URL {url} not allowed", "vpn_status": status}

    # Start selb_app.py in background thread
    Thread(target=run_selb_script, args=(username, password)).start()

    # Count currently running sessions
    running_count = count_running_sessions()

    return {
        "message": "SeleniumBase script started on Grid in background.",
        "current_sessions": running_count,
        "vpn_status": status
    }
    
def tail_log(file_path, lines=200):
    try:
        with open(file_path, "r") as f:
            all_lines = f.readlines()
            return "".join(all_lines[-lines:])
    except FileNotFoundError:
        return f"Log file '{file_path}' not found."
    except Exception as e:
        return f"Error reading log file: {str(e)}"
@app.get("/logs/")
async def get_logs(log_lines: int = Query(200, description="Number of log lines to return (default 200)")):
    logs = tail_log(LOG_FILE, lines=log_lines)
    return {"log_lines_returned": log_lines, "logs": logs}
