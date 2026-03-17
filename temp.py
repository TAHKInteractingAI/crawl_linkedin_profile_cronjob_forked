# import json
# import pandas as pd
# import re
# import os
# from oauth2client.service_account import ServiceAccountCredentials
# import gspread
# from dotenv import load_dotenv

# load_dotenv()
# """# **CONFIG**"""
# MAX_MESSAGES_PER_DAY = 15
# COOKIES_FILE = 'linkedin_cookies.pkl'
# # Thông tin bảng tính
# SPREADSHEET_ID = os.getenv('SPREADSHEET_MESS_ID')
# SHEET_NAME = 'Sheet1'
# RANGE_NAME = 'A:E'
# GOOGLE_CREDS = os.getenv('GOOGLE_APPLICATION_CRED')

# def get_data_with_links(sheet):
#     # 1. Lấy toàn bộ giá trị của bảng tính (để biết chính xác số dòng hiện có)
#     all_values = sheet.get_all_values()
#     if len(all_values) < 2:
#         return pd.DataFrame()

#     headers = all_values[1]  # Dòng 2 (index 1) là header
#     data_rows = all_values[2:] # Dữ liệu thực tế từ dòng 3
#     num_rows = len(data_rows)

#     # 2. Lấy metadata của cột E (Attachment) - Giả sử là cột số 5
#     # Chỉ lấy đúng phạm vi tương ứng với số dòng dữ liệu đang có
#     spreadsheet = sheet.spreadsheet
#     sheet_name = sheet.title
#     range_metadata = f"{sheet_name}!E3:E{2 + num_rows}"
    
#     res_metadata = spreadsheet.fetch_sheet_metadata({
#         'includeGridData': True,
#         'ranges': [range_metadata]
#     })
    
#     links_per_row = []
#     # Truy cập vào cấu trúc dữ liệu JSON của Google
#     sheets_data = res_metadata.get('sheets', [])[0].get('data', [])[0]
#     rowData = sheets_data.get('rowData', [])
    
#     for row in rowData:
#         cell_links = []
#         values = row.get('values', [])
#         if values:
#             cell = values[0]
#             # Ưu tiên 1: Link bao trùm toàn bộ ô
#             if 'hyperlink' in cell:
#                 cell_links.append(cell['hyperlink'])
#             # Ưu tiên 2: Nhiều link trong các đoạn văn bản (Rich Text)
#             elif 'textFormatRuns' in cell:
#                 for run in cell['textFormatRuns']:
#                     url = run.get('format', {}).get('link', {}).get('uri')
#                     if url:
#                         cell_links.append(url)
        
#         # Gộp các link, loại bỏ trùng lặp bằng set
#         unique_links = list(dict.fromkeys(cell_links))
#         links_per_row.append(", ".join(unique_links))

#     # 3. Đảm bảo links_per_row có độ dài bằng với data_rows
#     # Nếu metadata trả về thiếu, bù cho đủ bằng chuỗi rỗng
#     while len(links_per_row) < num_rows:
#         links_per_row.append("")

#     # 4. Tạo DataFrame
#     df = pd.DataFrame(data_rows, columns=headers)
    
#     # Cập nhật cột Attachment (cần chắc chắn tên cột đúng 100% với file Sheets)
#     if 'Attachment' in df.columns:
#         df['Attachment'] = links_per_row[:num_rows]
    
#     return df

# # Xác thực với Google Sheets API
# scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# info = json.loads(GOOGLE_CREDS)
# creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
# client = gspread.authorize(creds)

# # Lấy dữ liệu từ bảng tính
# sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Sheet1')
# values = sheet.get_all_values()
# #df = pd.DataFrame(values[2:], columns=values[1])
# df = get_data_with_links(sheet)
# print(type(GOOGLE_CREDS))
# print(df['Attachment'])


# import selenium
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

# # 1. Kiểm tra phiên bản thư viện Selenium
# print(f"--- THÔNG TIN PHIÊN BẢN ---")
# print(f"1. Selenium Version: {selenium.__version__}")

# try:
#     # 2. Khởi tạo driver để kiểm tra phiên bản trình duyệt và driver
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service)

#     # 3. Lấy thông tin từ driver
#     caps = driver.capabilities
#     print(f"2. Browser Name: {caps['browserName']}")
#     print(f"3. Browser Version: {caps['browserVersion']}")
#     print(f"4. ChromeDriver Version: {caps['chrome']['chromedriverVersion'].split(' ')[0]}")
    
#     driver.quit()
#     print("---------------------------")
#     print("Kết quả: Các phiên bản đã được liệt kê ở trên.")

# except Exception as e:
#     print(f"Lỗi khi kiểm tra: {e}")

from copy_of_message_linkedin_with_cookie import get_missive_linkedin_code
a = get_missive_linkedin_code()
#d = [c for c in a if 'name' in c['authors'][0] and c['authors'][0]['name'] == 'LinkedIn']
print(a)
print(type(a))

# if __name__ == "__main__":
#     # code = get_missive_linkedin_code()
#     # print(f"LINKEDIN_CODE={code}")
#     get_missive_linkedin_code()