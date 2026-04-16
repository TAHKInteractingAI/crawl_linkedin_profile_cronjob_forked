import os
import time
import pickle
import random
import json
import PIL
from dotenv import load_dotenv
import requests
# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
import google.generativeai as genai
import undetected_chromedriver as uc
from lxml import html
# Google APIs / Sheets
import gspread
from google.auth import default
from googleapiclient.discovery import build
from google.oauth2 import service_account
import google.api_core.exceptions as google_exceptions
# Guard Colab imports
try:
    from google.colab import auth, files  # type: ignore
    _IS_COLAB = True
except Exception:
    auth = None
    files = None
    _IS_COLAB = False

# Optional: IPython display (only in notebooks)
try:
    from IPython.display import Image, display  # type: ignore
except Exception:
    Image = None
    display = None

load_dotenv(override=True)

# --- CẤU HÌNH ---
INPUT_TAB_NAME = "Sheet1"
MISSIVE_API_KEY = os.getenv('MISSIVE_API_KEY')
TARGET_URL = "https://www.linkedin.com/uas/login?session_redirect=https%3A%2F%2Fwww.linkedin.com%2Ffeed%2F"
HEADERS = {"Authorization": f"Bearer {MISSIVE_API_KEY}", "Content-Type": "application/json"}
PARAMS = {"limit": 20, "inbox":"true"} 
CREDENTIALS_FILE = 'linkedin_credentials.pkl'
SPREADSHEET_CRAWL_ID = os.getenv('SPREADSHEET_CRAWL_ID')
GOOGLE_CREDS = os.getenv('GOOGLE_APPLICATION_CRED') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_PROMPT = """
                From the image, extract company names and positions that are currently the user working on until present.
                Response by giving 2 seperated lists, one for company names and one for positions. Format the list of postions with 'from'
                Here's the example format: [<company1>, <company2>,..etc]|[<position1> from <company1>, <position2> from <company1>, <position1> from <company2>, <position2> from <company2>,..etc]
                Response only with the lists, no additional text.
                
                """

ACCOUNTS = [
    {
        "user": os.getenv("LINKEDIN_USERNAME_1"),
        "pass": os.getenv("LINKEDIN_PASSWORD"),
        "cookie_filename": "cookies_acc1.pkl"
    },
    {
        "user": os.getenv("LINKEDIN_USERNAME_2"),
        "pass": os.getenv("LINKEDIN_PASSWORD"),
        "cookie_filename": "cookies_acc2.pkl"
    }
]

XPATH_USERNAME = '//*[@id="username"] | //input[@id=":r3:"]'
XPATH_PASSWORD = '//*[@id="password"] | //input[@id=":r4:"]'
XPATH_LOGIN_BUTTON = '//button[contains(@class, "btn__primary--large") and @aria-label="Sign in"] | /html/body/div[1]/div[2]/div/div/div/main/div/div[2]/div/div[1]/div/div/div[2]/div/div/div/div[2]/div/div[3]/button'# //button[contains(., "Sign in") and not(contains(., "Google")) and not(contains(., "Apple"))]'

TITLE_XPATH = '/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[1]/div[1]/div/p[1]'
COMPANY_XPATH = '/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div/p'
EXPERIENCE_CARD_XPATH = "/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[6]/div/div/div[1]/div/section/div/div[2]/div[1]/h2 | /html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[5]/div/div[1]/div/section/div/div[2]/div[1]/h2"
XPATH_LOCATION = '/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[1]/div[1]/div/div[2]/p[1]'
XPATH_TITLE = '/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[1]/div[1]/div/p[1]'
# --- 1. SETUP DRIVER ---
# def get_driver():
#     options = webdriver.ChromeOptions()
    
#     # 1. Định nghĩa một User-Agent nhất quán (Tránh khai báo 2 lần)
#     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     options.add_argument(f"user-agent={user_agent}")

#     # 2.1 Các thiết lập cơ bản cho môi trường Linux/Docker (GitHub Actions)
#     options.add_argument('--no-sandbox')
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument('--disable-gpu')
#     options.add_argument('--headless=new')
#     options.add_argument("--window-size=1920,1080")
#     options.page_load_strategy = 'eager'
#     # 2.2 Ép trình duyệt và Header luôn yêu cầu tiếng Anh (vài text button không phải tiếng anh)
#     options.add_argument('--lang=en-GB') 
#     options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_GB'})
    
#     # 3. CHỐNG PHÁT HIỆN BOT (Stealth Mode)
#     # Loại bỏ cờ 'nút điều khiển tự động'
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     # Vô hiệu hóa tính năng AutomationControlled của Blink
#     options.add_argument("--disable-blink-features=AutomationControlled")
    
#     # Thêm các cờ để trình duyệt giống người dùng thật hơn
#     options.add_argument("--disable-infobars")
#     options.add_argument("--disable-notifications")
    
#     # Khởi tạo driver
#     driver = webdriver.Chrome(options=options)
    
#     # 4. Ẩn thuộc tính navigator.webdriver bằng Script thực thi ngay khi load trang
#     driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#         "source": """
#             Object.defineProperty(navigator, 'webdriver', {
#                 get: () => undefined
#             })
#         """
#     })
    
#     return driver
def get_driver():
    options = uc.ChromeOptions()
    
    # 1. Cấu hình cơ bản cho môi trường Headless (GitHub Actions)
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    
    # 2. [TĂNG TỐC] Chiến lược load trang
    # 'eager' giúp trình duyệt không chờ đợi tải xong ảnh hay script bên thứ 3
    options.page_load_strategy = 'normal'
    
    # 3. [TĂNG TỐC] Chặn tải hình ảnh, CSS và Fonts để tiết kiệm băng thông và RAM
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 1,
        "profile.managed_default_content_settings.fonts": 2
    }
    options.add_experimental_option("prefs", prefs)
    
    # 4. Ép trình duyệt dùng tiếng Anh
    options.add_argument('--lang=en-GB')
    
    # 5. [CHỐNG PHÁT HIỆN] Thêm Proxy dân cư (Khuyến nghị)
    # Trên GitHub Actions, hãy set secrets.PROXY_URL (ví dụ: http://user:pass@ip:port)
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        options.add_argument(f'--proxy-server={proxy_url}')
    
    # Khởi tạo undetected_chromedriver (Không dùng webdriver.Chrome thông thường)
    driver = uc.Chrome(options=options, version_main=146)
    
    # 6. [CHỐNG PHÁT HIỆN] Bơm thêm Stealth Script qua CDP
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            // Ẩn webdriver
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Fake runtime của Chrome (Bot thường không có cái này)
            window.navigator.chrome = { runtime: {} };
            
            // Bơm thêm plugins giả
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Ép ngôn ngữ
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en-US', 'en']
            });
        """
    })
    
    return driver

# --- 2. KẾT NỐI GOOGLE SHEET ---
def connect_google_sheet():
    try:
        # If running in Colab use its auth flow, otherwise use service account
        if _IS_COLAB and auth is not None:
            auth.authenticate_user()
            creds, _ = default()
            gc = gspread.authorize(creds)
        else:
            # Expect GOOGLE_CREDS to contain service account JSON
            if not GOOGLE_CREDS:
                raise RuntimeError("No GOOGLE_CREDS set for service account authentication")
            info = json.loads(GOOGLE_CREDS)
            creds = service_account.Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            gc = gspread.authorize(creds)
        sh = gc.open_by_url(SPREADSHEET_CRAWL_ID) if "http" in SPREADSHEET_CRAWL_ID else gc.open_by_key(SPREADSHEET_CRAWL_ID)
        return sh
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Sheet: {e}")
        return None

def human_type(element, text):
    """Gõ phím như người thật với độ trễ ngẫu nhiên"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))

def save_cookies(driver):
    """Lưu cookies vào file"""
    with open(COOKIES_FILE, "wb") as cookies_file:
        pickle.dump(driver.get_cookies(), cookies_file)
    print("INFO: COOKIES SAVED!")

def load_cookies(driver: webdriver.Chrome, file_name: str):
    """Đọc cookies từ file pickle và thêm vào browser"""
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
def handle_cookie_acceptance(driver: webdriver.Chrome):
    """Xử lý chấp nhận cookies nếu có"""
    try:
        driver.find_element(By.XPATH, "//button[span[text()='Accept']]").click()
        print("INFO: COOKIES IS ACCEPTED!")
    except:
        print("INFO: COOKIES IS NOT REQUIRED!")

def handle_code_verification(driver: webdriver.Chrome):
    """Chỉ xử lý nếu thấy ô nhập mã, không để bị timeout treo script"""
    try:
        # Giảm timeout xuống thấp (5s) vì nếu có code, nó sẽ hiện ra ngay
        ID_FIELD = "input__email_verification_pin"
        verification_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, ID_FIELD))
        )
        
        print("➡️ Phát hiện yêu cầu mã PIN. Đang lấy code...")
        code = get_missive_linkedin_code()
        print(f"PIN: {code}")
        if code:
            verification_field.send_keys(code)
            driver.find_element(By.ID, "email-pin-submit-button").click()
            time.sleep(10)
        else:
            print("❌ Không lấy được mã PIN từ Missive.")
    except TimeoutException:
        print("✅ Không yêu cầu mã PIN, bỏ qua bước này.")
        
def get_missive_linkedin_code():
    response = requests.get("https://public.missiveapp.com/v1/conversations", headers=HEADERS, params=PARAMS)
    if response.status_code != 200:
        return f"Lỗi API: {response.status_code}"
    conversations = response.json().get("conversations", [])
    temp = [c['latest_message_subject'] for c in conversations if 'name' in c['authors'][0] and c['authors'][0]['name'] == 'LinkedIn']
    final_temp = [f.split(' ')[-1:][0] for f in temp]
    for item in final_temp:
        if item.isdigit():
            return item
    return None

def check_account_status(driver: webdriver.Chrome):
    """Kiểm tra trạng thái tài khoản một cách chính xác hơn"""
    time.sleep(15) # Đợi một chút để trang ổn định
    current_url = driver.current_url
    
    # 1. Kiểm tra các URL báo khóa/chặn
    if any(x in current_url for x in ["checkpoint", "challenge", "disabled"]):
        return "LOCKED"
    
    # 2. Kiểm tra dấu hiệu login thành công (URL chứa /feed/ hoặc có thanh tìm kiếm)
    if "/feed" in current_url or "/search" in current_url:
        return "LOGGED_IN"
        
    # 3. Kiểm tra bằng element (dùng selector bền vững hơn)
    try:
        # Kiểm tra thanh search hoặc icon 'Home' thay vì chỉ avatar
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
        )
        return "LOGGED_IN"
    except:
        return "UNKNOWN"
def login_failover(driver: webdriver.Chrome):
    global COOKIES_FILE
    for acc in ACCOUNTS:
        time.sleep(random.uniform(8, 10)) # Delay ngẫu nhiên trước khi thử account mới
        if not acc["user"] or not acc["pass"]:
            continue
            
        username = acc["user"]
        password = acc["pass"]
        COOKIES_FILE = acc["cookie_filename"]
        
        print(f"\n🚀 Đang thử tài khoản: {username}")

        # --- BƯỚC 1: THỬ COOKIE ---
        if os.path.exists(COOKIES_FILE):
            print(f"DEBUG: Nạp cookie từ {COOKIES_FILE}")
            try:
                driver.get(TARGET_URL) # Phải vào domain trước khi add cookie
                load_cookies(driver, COOKIES_FILE)
                driver.refresh()
                time.sleep(5)
                #driver.get("https://www.linkedin.com/feed")
                status = check_account_status(driver)
                if status == "LOGGED_IN":
                    print(f"✅ Login thành công bằng COOKIE cho {username}")
                    driver.save_screenshot(f"cookie_login_{username}.png")
                    return True
                else:
                    driver.save_screenshot(f"cookie_login_failed_{username}.png")
                    print(f"⚠️ Cookie cũ không hiệu lực. Đang xóa file {COOKIES_FILE}...")
                    os.remove(COOKIES_FILE) # Xóa ngay nếu không dùng được
            except Exception as e:
                print(f"⚠️ Có lõi khi dùng cookies cho  {username}: {e}")
                driver.save_screenshot(f"cookie_login_failed_{username}.png")
                if os.path.exists(COOKIES_FILE):
                    try:
                        os.remove(COOKIES_FILE)
                    except Exception:
                        pass
                continue

        # --- BƯỚC 2: LOGIN THỦ CÔNG ---
        print(f"DEBUG: Tiến hành Login thủ công cho {username}")
        driver.get(TARGET_URL)
        
        try:
            u_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, XPATH_USERNAME)))
            human_type(u_field, username)
            time.sleep(2)
            p_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, XPATH_PASSWORD)))
            human_type(p_field, password)
            time.sleep(2)
            # Click Login
            btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, XPATH_LOGIN_BUTTON)))
            btn.click()
            time.sleep(15)
            # Kiểm tra 2FA Verification
            handle_code_verification(driver)
            
            # Kiểm tra kết quả cuối cùng
            status = check_account_status(driver)
            if status == "LOGGED_IN":
                handle_cookie_acceptance(driver)
                save_cookies(driver) # Lưu lại cookie mới của account này
                driver.save_screenshot(f"manual_login_{username}.png")
                print(f"✅ Đã lưu cookie mới cho {username}")
                return True
            else:
                print(f"❌ Tài khoản {username} bị KHÓA hoặc Checkpoint. Đang đổi account...")
                driver.save_screenshot(f"cookie_login_failed_{username}.png")
                if os.path.exists(COOKIES_FILE):
                    os.remove(COOKIES_FILE)
                continue # Nhảy sang loop account tiếp theo
                
        except Exception as e:
            print(f"❌ Lỗi trong khi login thủ công {username}: {str(e)}")
            driver.save_screenshot(f"cookie_while_login_failed_{username}.png")
            if os.path.exists(COOKIES_FILE):
                try:
                    os.remove(COOKIES_FILE)
                except Exception:
                    pass
            continue

    print("‼️ HẾT TÀI KHẢN KHẢ DỤNG. DỪNG CHƯƠNG TRÌNH.")
    return False
#'gemini-3-flash-preview','gemini-3.1-flash-lite-preview', 'gemini-2.5-flash-lite'
AVAILABLE_MODELS = ['gemini-3-flash-preview','gemini-3.1-flash-lite-preview', 'gemini-2.5-flash-lite']
def call_gemini_with_image(image_path) -> list:
    img = PIL.Image.open(image_path)
    #genai.configure(api_key=GEMINI_API_KEY)
    for model_name in AVAILABLE_MODELS:
        try:
            print(f"--- Đang thử model: {model_name} ---")
            model = genai.GenerativeModel(model_name)
            print(f"--- Đang sử dụng model: {model_name} ---, --- Keys: {GEMINI_API_KEY}")
            response = model.generate_content([GEMINI_PROMPT, img]).text
            
            # Xử lý chuỗi trả về
            parts = response.split('|')
            if len(parts) < 2: continue # Nếu format sai thì thử model khác hoặc bỏ qua
            
            coms = parts[0].strip(' []').replace("'", "").replace('"', '')
            poss = parts[1].strip(' []').replace("'", "").replace('"', '')
            
            print(f"✅ Thành công với {model_name}. Công ty: {coms}, Vị trí: {poss}")
            return coms, poss

        except google_exceptions.ResourceExhausted:
            #print(f"⚠️ Model {model_name} đã hết quota (Reached Quota).")
            continue 
        except Exception as e:
            #print(f"❌ Lỗi với {model_name}: {str(e)}")
            continue

    print("🛑 Tất cả model đều thất bại hoặc hết quota. Chuyển sang XPATH...")
    return None, None

# --- 4. CRAWL PROFILE ---
def scroll_linkedin(driver, pixels):
    # Script này tìm khung cuộn của LinkedIn và kéo xuống
    scroll_script = f"""
        var container = document.querySelector('main') || document.querySelector('.scaffold-layout__main') || window;
        container.scrollBy(0, {pixels});
    """
    driver.execute_script(scroll_script)
    
def scroll_linkedin_XPATH(driver):
    # Sử dụng XPath dựa trên cấu trúc trong file của bạn
    # Tìm thẻ h2 chứa chữ "Experience" 
    
    try:
        # Tìm element trước trong Python
        element = driver.find_element("xpath", EXPERIENCE_CARD_XPATH)
        
        # Truyền element vào script thông qua tham số arguments[0]
        driver.execute_script("""
            arguments[0].scrollIntoView({
                behavior: 'smooth', 
                block: 'center'
            });
        """, element)
        print("Đã scroll đến phần Experience thành công.")
    except Exception as e:
        print(f"Không tìm thấy phần Experience để scroll: {e}")
        
def crawl_profile(driver, raw_url):
    try:
        url = raw_url.strip()
        driver.get(url)

        print(f"--- Processing: {url}")
        # Chờ trang tải nội dung cơ bản (chỉ 8-12s)
        time.sleep(random.uniform(8, 12))
        
        scroll_linkedin_XPATH(driver)
        
        time.sleep(2)
        driver.save_screenshot(f"screenshot_temp.png")

        if any(x in driver.current_url for x in ["login", "authwall", "checkpoint", "challenge"]):
            print("Debug: Auth wall detected.")
            # Chụp screenshot lưu lại log trên GitHub Actions
            filename = f"authwall_{int(time.time())}.png"
            driver.save_screenshot(filename)
            print(f"Screenshot saved: {filename}")
            return None, "AUTH_WALL"

        # Khối JavaScript trích xuất dữ liệu của bạn
        data_js = driver.execute_script("""
        const getTxt = (el) => el ? el.innerText.trim() : "";
        const getElementByTextLength = (selector, maxLength) => {
        return [...document.querySelectorAll(selector)]
        .find(el => (el.innerText?.trim().length || 0) <= maxLength);
        };
        const nameElement = getElementByTextLength('a:has(h2)', 20) || getElementByTextLength('a:has(h1)', 20);
        const name = getTxt(nameElement);

        const keywords = ['connections', 'followers'];
        const connections = [...document.querySelectorAll('p')]
          .find(p => /connections|followers/i.test(p.innerText))
          ?.closest('div')?.innerText;

          const items = document.querySelectorAll('[componentkey^="entity-collection-item"]');
          const currentCompanies = Array.from(items)
          .filter(item => {
              const text = item.innerText.toLowerCase();
              return text.includes('present') || text.includes('hiện tại');
          })
          .map(item => {
              const logoEl = item.querySelector('[aria-label$="logo"], img[alt$="logo"]');
              if (logoEl) {
              const labelText = logoEl.getAttribute('aria-label') || logoEl.getAttribute('alt');
              if (labelText) {
                  return labelText.replace(/\s+logo$/i, '').trim();
              }
              }
              const pTags = Array.from(item.querySelectorAll('p'))
                    .map(p => p.innerText.trim())
                    .filter(t => t.length > 0);
              if (pTags.length > 1) {
              return pTags[1].split(' · ')[0].trim();
              }
              return "";
          })
          .filter(name => name !== "");
          
          return {
          name: name,
          connections: connections,
          company: currentCompanies
          };
        """)

        name = data_js.get('name', '')
        
        
        location_el = WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.XPATH, XPATH_LOCATION)))
        location = location_el.text.strip()

        company, title = call_gemini_with_image(image_path='screenshot_temp.png')
        print(f"Thông tin công ty: {company}, Chức vụ: {title}")
        #     title_el = WebDriverWait(driver, 6).until(
        #     EC.presence_of_element_located((By.XPATH, XPATH_TITLE))
        # )
        #     title = title_el.text.strip()
            # company = data_js.get('company', '')
        if company == None or title == None:
            print(f"--- Đang trích xuất theo logic Visual-Order ---")
            tree = html.fromstring(driver.page_source)
            current_companies_list = []
            job_titles_list = []

            time_labels = tree.xpath("//span[contains(., 'Present') or contains(., 'Hiện tại')] | //p[contains(., 'Present') or contains(., 'Hiện tại')]")
            
            processed_containers = set()

            for label in time_labels:
               
                container = label.xpath("./ancestor::li[contains(@class, 'artdeco-list__item')] | ./ancestor::div[contains(@componentkey, 'entity-collection-item')]")
                
                if container:
                    cont = container[0]
                    if cont in processed_containers: continue
                    processed_containers.add(cont)

                    all_spans = cont.xpath(".//span[@aria-hidden='true']/text() | .//p/text()")
                    clean_info = [s.strip() for s in all_spans if s.strip() and len(s.strip()) > 1]

                    parent_li = cont.xpath("./ancestor::li[contains(@class, 'artdeco-list__item')]")
                    
                    if parent_li: 
                        p_comp = parent_li[0].xpath(".//a[1]//span[@aria-hidden='true']/text()")
                        c_name = p_comp[0].strip() if p_comp else ""
                        t_name = clean_info[0] if clean_info else ""
                    else: 

                        t_name = clean_info[0] if len(clean_info) > 0 else ""
                        c_name = clean_info[1].split('·')[0].strip() if len(clean_info) > 1 else ""

                    if c_name != "" and t_name != "":
                        if c_name not in current_companies_list:
                            current_companies_list.append(c_name)
                        job_titles_list.append(f"{t_name} from {c_name}")
                        
            company = ", ".join(current_companies_list) if current_companies_list else ""
            title = ", ".join(job_titles_list) if job_titles_list else ""

            if title == "":
                print("Không tìm thấy tiêu đề, sử dụng XPATH")
                title_xpath = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TITLE_XPATH)))
                title = title_xpath.text.strip() if title_xpath else "No Title"
            if company == "":
                print("Không tìm thấy công ty, sử dụng XPATH")
                company_xpath = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, COMPANY_XPATH)))
                company = company_xpath.text.strip() if company_xpath else "No Company"
            print(f"✅ Kết quả: Companies [{company}] | Titles [{title}]")

        conn_source = data_js.get('connections', '').strip()
        parts = conn_source.split()
        clean_connection = " ".join([p for p in parts if p != '·'])
        
        print(f"""
              =================
              Đã cào: {url}
              Tên: {name}
              Tiêu đề: {title}
              Địa điểm: {location}
              Kết nối: {clean_connection}
              Công ty: {company}
              =================
              """)

        return {
            "Name": name, "Title": title, "Location": location, "Connection": clean_connection, "Company": company
        }, "Success"

    except Exception as e:
        print(f"Debug: Lỗi trích xuất tại {url} - {str(e)}")
        return None, str(e)
# --- 5. MAIN ---
def main():
    MAX_PROFILE = 2
    count = 0
    sh = connect_google_sheet()
    if not sh: return
    ws = sh.worksheet(INPUT_TAB_NAME)
    urls = ws.col_values(1)
    names = ws.col_values(2)
    titles = ws.col_values(3)
    locations = ws.col_values(4)
    connections = ws.col_values(5)
    companies = ws.col_values(6)
    
    # Use get_driver which configures ChromeOptions for headless/stealth
    driver = get_driver()
    if not login_failover(driver):  return

    for i in range(1, len(urls)):
        url = urls[i]
        if "linkedin.com/in/" not in url: continue
        #Nếu tất cả đã có dữ liệu thì bỏ qua
        name_val = names[i] if i < len(names) else ""
        title_val = titles[i] if i < len(titles) else ""
        loc_val = locations[i] if i < len(locations) else ""
        conn_val = connections[i] if i < len(connections) else ""
        comp_val = companies[i] if i < len(companies) else ""
        if name_val and title_val and loc_val and conn_val and comp_val:
            continue
        print(f"🔄 Đang xử lý: {url}")
        
        # Trong vòng lặp for i in range(1, len(urls)) của hàm main:
        data, status = crawl_profile(driver, url)
        
        if status == "Success" and data and data['Name']:
            print(f"   ✅ OK")
            try:
                ws.update(range_name=f"B{i+1}:F{i+1}", values=[[
                    data['Name'], data['Title'], data['Location'], f"{data['Connection']}", f"{data['Company']}"
                ]])
            except Exception as e:
                print(f"  ⚠️ Lỗi cập nhật Sheet cho {url}: {str(e)}")  
        else:
            # Nếu status là Success nhưng Name rỗng thì vẫn coi là lỗi selector
            error_msg = status if status != "Success" else "SELECTOR_FAILED"
            print(f"   ❌ Lỗi cho {url}: {error_msg}")
            try:
                ws.update_cell(i+1, 2, f"Error: {error_msg}")
            except:
                pass
            if error_msg == "AUTH_WALL": 
                print("🛑 Phát hiện Auth Wall, dừng đợt này để bảo vệ acc.")
                break

        count +=1
        if count >= MAX_PROFILE:
            print("reached max limit")
            break

        time.sleep(random.randint(40, 80))

    driver.quit()
    
if __name__ == "__main__":
    main()
    print("👌👌👌👌THỰC THI XONG CHƯƠNG TRÌNH!")