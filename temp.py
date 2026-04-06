# import google.generativeai as genai
# import PIL.Image

# genai.configure(api_key="")
# model = genai.GenerativeModel('gemini-3-flash-preview')

# img = PIL.Image.open('capture.png')
# # Bạn có thể đưa prompt tùy ý để trích xuất dữ liệu
# response = model.generate_content(["Trích xuất ảnh và cho tôi chức vụ và tên công ty cho những mục có 'present'. Format theo JSON: '<tên công ty>', 'chức vụ':'<chức vụ>'. Response chỉ json, ngắn gọn, không thêm nội dung khác vào", img])
# print(response.text)
import re
a = str("""
        ```json
[
  {
    "tên công ty": "Arkweaver",
    "chức vụ": "CEO and Co-Founder"
  },
  {
    "tên công ty": "Various Startups",
    "chức vụ": "Fractional Leadership for AI Companies"
  }
]
```
""")
# remove ''' and 'json'
a = re.sub(r"```json|```", "", a).strip()
print(a)