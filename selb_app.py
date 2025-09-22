
import time, random, os, sys, json, logging, traceback
from seleniumbase import SB
from seleniumbase import BaseCase
import boto3
import botocore
from datetime import datetime, timedelta
from urllib.parse import urlparse
def rand_sleep(first=1, second=3):
    time.sleep(random.uniform(first, second))
if getattr(sys, 'frozen', False):
    script_directory = os.path.dirname(sys.executable)
else:
    script_directory = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_directory, "app.log")
SESSION_FILE = os.path.join(script_directory, "storage_state.json")
REPORTS_FOLDER = os.path.join(script_directory, "downloaded_files")
os.makedirs(REPORTS_FOLDER, exist_ok=True)
logger = logging.getLogger("customLogger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(file_handler)

def pwrite(*args, p=True):
    message = " ".join(str(a) for a in args)
    logger.info(message)
    if p:
        print(message)
for filename in os.listdir(REPORTS_FOLDER):
    file_path = os.path.join(REPORTS_FOLDER, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            import shutil
            shutil.rmtree(file_path)
    except Exception as e:
        pwrite(f"⚠️ Failed to delete {file_path}: {e}")
image_folder = os.path.join(script_directory, "Error_Screenshots")
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

pwrite('Started')

# def get_credentials():
#     parser = argparse.ArgumentParser(description="Login credentials")
#     parser.add_argument("--username", help="Username for login")
#     parser.add_argument("--password", help="Password for login")
#     parser.add_argument("positional", nargs="*", help="Positional username and password")
#     args = parser.parse_args()
#     username = args.username
#     password = args.password
#     if not username or not password:
#         if len(args.positional) >= 2:
#             username = args.positional[0]
#             password = args.positional[1]
#     if not username or not password:
#         sys.exit("❌ Please provide both username and password (via args or position).")
#     return username, password

jan_current = [
"https://eddinscounseling.janeapp.com/admin#reports/appointments",
"https://eddinscounseling.janeapp.com/admin#reports/online_appointments",
"https://eddinscounseling.janeapp.com/admin#reports/retention",
"https://eddinscounseling.janeapp.com/admin#reports/unscheduled_patients",
"https://eddinscounseling.janeapp.com/admin#reports/wait_list",
"https://eddinscounseling.janeapp.com/admin#reports/shift",
"https://eddinscounseling.janeapp.com/admin#reports/compensation",
"https://eddinscounseling.janeapp.com/admin#reports/timesheets",
"https://eddinscounseling.janeapp.com/admin#reports/billings",
"https://eddinscounseling.janeapp.com/admin#reports/sales",
"https://eddinscounseling.janeapp.com/admin#reports/sales/by_staff_member",
"https://eddinscounseling.janeapp.com/admin#reports/transactions",
"https://eddinscounseling.janeapp.com/admin#reports/applied_unapplied_payments",
"https://eddinscounseling.janeapp.com/admin#reports/stripe_charges",
"https://eddinscounseling.janeapp.com/admin#reports/adjustments",
"https://eddinscounseling.janeapp.com/admin#reports/write_off",
"https://eddinscounseling.janeapp.com/admin#reports/performance",
"https://eddinscounseling.janeapp.com/admin#reports/insurance_policies",
"https://eddinscounseling.janeapp.com/admin#reports/activity",
"https://eddinscounseling.janeapp.com/admin#patients"  
]

thirty_day_urls = [
  "https://eddinscounseling.janeapp.com/admin#reports/transactions/daily"
]
default_date_urls = [
"https://eddinscounseling.janeapp.com/admin#reports/accounts_receivable",
"https://eddinscounseling.janeapp.com/admin#reports/inventory",
"https://eddinscounseling.janeapp.com/admin#reports/credit",
"https://eddinscounseling.janeapp.com/admin#reports/gift_card",
"https://eddinscounseling.janeapp.com/admin#reports/gift_card_transactions",
"https://eddinscounseling.janeapp.com/admin#reports/packages/sales",
"https://eddinscounseling.janeapp.com/admin#reports/packages/usage"
]
def wait_for_download(filename_ext=".csv", timeout=30, max_age=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        now = time.time()
        fresh_files = []
        for f in os.listdir(REPORTS_FOLDER):
            if f.endswith(filename_ext):
                path = os.path.join(REPORTS_FOLDER, f)
                # File must be recent
                if now - os.path.getmtime(path) <= max_age:
                    fresh_files.append(path)

        if fresh_files:
            return max(fresh_files, key=os.path.getmtime)
        time.sleep(1)

    raise TimeoutError(f"No new {filename_ext} file found in {timeout} seconds")

def rename_file(filepath):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    new_name = f"Startrader_{timestamp}.xlsx"
    new_path = os.path.join(REPORTS_FOLDER, new_name)
    os.rename(filepath, new_path)
    return new_path



def rand_sleep(first=1, second=3):
    time.sleep(random.uniform(first, second))

def main():
    pwrite('Seleniumbase script started')
    
    username = os.getenv("SB_USERNAME")
    password = os.getenv("SB_PASSWORD")
    pwrite(f'username: {username} and password : {password}')

    with SB(uc=True,headless2=True, window_size="1600,5000", server="localhost", port=4444) as sb: #headless=True, 
            try:
                sb.uc_frame_switch_to_captcha_if_present()
            except:
                pass
            sb.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                    Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                    Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                """
            },
        )
            sb.uc_open("https://eddinscounseling.janeapp.com/admin#login")
            pwrite(f"opening https://eddinscounseling.janeapp.com/admin#login using undetected mode")
            # load_cookies(sb)
            # sb.refresh()
            rand_sleep(5,11)
            try:
                sb.press_keys('//*[@id="auth_key"]', username, by="xpath")
                pwrite('Writing Username')
                rand_sleep(1,3)
                sb.press_keys('//*[@id="password"]', password, by="xpath")
                pwrite(f'Writing Password')
                rand_sleep(1,3)
                sb.uc_click('//button[@type="submit"]', by="xpath")
                rand_sleep(5,10)
                try:
                    sb.press_keys('//*[@id="password"]', password, by="xpath")
                    rand_sleep(1,3)
                    sb.uc_click('//button[@type="submit"]', by="xpath")
                except:
                    pass
                rand_sleep(7,14)
                pwrite("[INFO] Login successful")
                #save_cookies(sb)            
            except:
                pass
            sb.save_screenshot("screenshot.png")
            pwrite("Starting January to Current date range reports")
            def make_click(xpathe, t=10, sleep_time=None):
            
                sb.wait_for_element(xpathe, timeout=t)
                if sleep_time is not None:
                    time.sleep(sleep_time)
                sb.click(xpathe,  timeout=t)
                pwrite(f"Clicked on element: {xpathe}")
            def write_error(url, error_message):
                parsed_url = urlparse(url)
                path_after_admin = parsed_url.fragment or parsed_url.path.split("/admin")[-1]
                path_after_admin = path_after_admin.strip("/").replace("/", "_")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename_prefix = f"{path_after_admin}_{timestamp}"
                sb.save_screenshot(os.path.join(image_folder, f"{filename_prefix}_screenshot.png"))
                with open("errors.log", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} - URL: {url} - Screenshot: {filename_prefix}_screenshot.png - Error: {error_message}\n")
            def download_report(url):
                original_window = sb.driver.current_window_handle
                handles_before = sb.driver.window_handles
                try:
                    make_click('//*[@class="button-generic filter-bar-button dropdown-toggle"]')
                except:
                    pwrite("Three dots dropdown button to download report not found")
                    write_error(url, 'Three dots dropdown button to download report not found')
                    return False
                rand_sleep(1,3)
                try:
                    make_click('//*[text()="Export to CSV"]', t=10)
                except:
                    pwrite("Export to CSV button not found")
                    write_error(url, 'Export to CSV button not found')
                    return False            
                rand_sleep(1,3)
                if 'https://eddinscounseling.janeapp.com/admin#reports/gift_card_transactions'  in url:
                    return            
                # wait for new tab to open
                
                for _ in range(30):  # retry up to ~30 seconds
                    handles_after = sb.driver.window_handles
                    if len(handles_after) > len(handles_before):
                        new_window = [h for h in handles_after if h not in handles_before][0]
                        sb.driver.switch_to.window(new_window)
                        break
                    rand_sleep(1, 2)
                else:
                    pwrite("New tab did not open")
                    write_error(url, "New tab did not open")
                    return False
                make_click('//a[contains(@href,"/downloads")]', t=180)
                pwrite("Clicked on download link in new tab")
                all_tabs = sb.driver.window_handles
                for handle in all_tabs:
                    if handle != original_window:
                        try:
                            sb.driver.switch_to.window(handle)
                            sb.driver.close()
                        except Exception as e:
                            pwrite(f"Error closing tab: {e}")
                # Ensure back to original (or last remaining)
                remaining_tabs = sb.driver.window_handles
                sb.driver.switch_to.window(remaining_tabs[0])
                pwrite("Closed the new tab after download")
                
                
                
                
            for url in jan_current:
                sb.uc_open(url)
                rand_sleep(3,9)
                pwrite(f"Visiting {url}")
                try:
                    try:
                        make_click('//*[@data-test-id="filter-reset"]//*[text()="Reset"]', t=5)
                    except:
                        pass
                    try:
                        sb.wait_for_element('//*[@data-testid="date-range-picker-button" or @class="button-generic filter-bar-button dropdown-toggle"]', timeout=30)
                    except:
                        pwrite(f'Date Picker and Three Dots button not found on {url}')
                        write_error(url, 'Date Picker and Three Dots button not found')
                        continue
                    make_click('//*[@data-testid="date-range-picker-button"]')
                    rand_sleep(1,3)
                    try:
                        current_month_el = sb.wait_for_selector('(//*[@class="react-datepicker__current-month"])[1]', timeout=10).text
                    except:
                        make_click('//*[@data-testid="date-range-picker-button"]')
                        rand_sleep(1,3)

                    for i in range(12):
                        current_month_el = sb.wait_for_selector('(//*[@class="react-datepicker__current-month"])[1]', timeout=10).text
                        current_month = current_month_el.strip()
                        pwrite(f"Past month: {current_month}")
                        if "January" in current_month:
                            make_click('//*[@aria-label="Choose Wednesday, January 1st, 2025"]')
                            break
                        else:
                            make_click('//*[@aria-label="Previous Month"]')
                            rand_sleep(0.3,0.7)
                    rand_sleep(1,3)
                    today = datetime.today()            
                    day = today.day
                    month = today.strftime("%B") 
                    year = today.year
                    for i in range(12):
                        current_month_el = sb.wait_for_selector('(//*[@class="react-datepicker__current-month"])[2]', timeout=10).text
                        current_month = current_month_el.strip()
                        pwrite(f"Future month: {current_month}")
                        if month in current_month and str(year) in current_month:
                            make_click(f'.react-datepicker__day--today:not([class*="--outside-month"])')
                            break
                        else:
                            make_click('//*[@aria-label="Next Month"]')
                            rand_sleep(0.3,0.7)
                    rand_sleep(10,13)
                    
                    try:
                        sb.wait_for_selector('//table | //*[contains(@class, "table table-bordered") or @class="table-responsive"]', timeout=35)
                    except:
                        pwrite("Table not found:")
                    
                    download_report(url)                        
                    rand_sleep(15,20)
                except:
                    pwrite(f"Error processing {url}, moving to next\n\n {traceback.format_exc()}")
                    write_error(url, f"Error processing {url}, moving to next\n\n {traceback.format_exc()}")
            pwrite("Starting 30-day and default date range reports")
            for url in thirty_day_urls:
                    pwrite(f"Visiting {url}")
                    try:
                        sb.uc_open(url)
                        rand_sleep(3,9)
                        try:
                            make_click('//*[@data-test-id="filter-reset"]//*[text()="Reset"]', t=5)
                        except:
                            pass
                        today = datetime.today()
                        if 'https://eddinscounseling.janeapp.com/admin#reports/transactions/daily' in url:
                            past_date = today - timedelta(days=31)
                        else:
                            past_date = today - timedelta(days=30)
                        day_number = past_date.day
                        make_click('//*[@data-testid="date-range-picker-button"]')
                        rand_sleep(1,3)
                        make_click(f'(//*[@class="react-datepicker__month"])[1]//*[@aria-label and text()="{day_number}" and not (contains(@class, "outside-month"))]')
                        rand_sleep(1,3)
                        make_click(f'.react-datepicker__day--today:not([class*="--outside-month"])')
                        try:
                            sb.wait_for_selector('//table | //*[contains(@class, "table table-bordered") or @class="table-responsive"]', timeout=35)
                        except:
                            pwrite("Table not found:")
                        rand_sleep(5,13)
                        download_report(url)
                        rand_sleep(15,20)
                    except:
                        pwrite(f"Error processing {url}, moving to next\n\n {traceback.format_exc()}")
                        write_error(url, f"Error processing {url}, moving to next\n\n {traceback.format_exc()}")
            pwrite("Starting default date range reports")
            for url in default_date_urls:
                    pwrite(f"Visiting {url}")
                    try:
                        sb.uc_open(url)
                        rand_sleep(3,9)
                        try:
                            make_click('//*[@data-test-id="filter-reset"]//*[text()="Reset"]', t=5)
                        except:
                            pass
                        try:
                            sb.wait_for_selector('//*[@data-testid="date-range-picker-button" or @class="button-generic filter-bar-button dropdown-toggle"]', timeout=30)
                        except:
                            pwrite(f'Date Picker and Three Dots button not found on {url}')                        
                        rand_sleep(5,10)
                        try:
                            sb.wait_for_selector('//table | //*[contains(@class, "table table-bordered") or @class="table-responsive"]', timeout=35)
                        except:
                            pwrite("Table not found:")
                        download_report(url)
                                            
                        rand_sleep(15,20)
                    except:
                        pwrite(f"Error processing {url}, moving to next\n\n {traceback.format_exc()}")
                        write_error(url, f"Error processing {url}, moving to next\n\n {traceback.format_exc()}")
    time.sleep(5)
    endpoint = "https://mmayynuyhfvbcgofgnma.storage.supabase.co/storage/v1/s3"
    region = "us-east-2"

    access_key = "a509dd840f1603ee4aa65062b9935576"
    secret_key = "f2adc9cf33c13c246d6b277afddf3c2db6b8d82f241886573b8d2e84874b76dd"
    bucket_name = "selenium-reports"

    s3 = boto3.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    def ensure_bucket_exists(bucket):
        try:
            s3.head_bucket(Bucket=bucket)
            pwrite(f"✅ Bucket already exists: {bucket}")
        except botocore.exceptions.ClientError:
            pwrite(f"📦 Creating bucket: {bucket}")
            s3.create_bucket(Bucket=bucket)

    ensure_bucket_exists(bucket_name)
    def upload_csv_files(folder, bucket, user):
        if not os.path.exists(folder):
            pwrite(f"⚠️ Reports folder not found: {folder}")
            return

        files_uploaded = 0
        for file in os.listdir(folder):
            if file.lower().endswith(".csv"):
                file_path = os.path.join(folder, file)
                key = f"{user}/{file}"  # 👈 keep email as subfolder

                pwrite(f"⬆️ Uploading {file_path} → {bucket}/{key}")
                s3.upload_file(file_path, bucket, key)
                files_uploaded += 1

        if files_uploaded == 0:
            pwrite("⚠️ No CSV files found in folder.")
        else:
            pwrite(f"\n✅ Uploaded {files_uploaded} CSV file(s) to {bucket}/{user}/")

    upload_csv_files(REPORTS_FOLDER, bucket_name, username)
try:
    main()
except:
    import traceback
    pwrite(f'{traceback.format_exc()}')
