import google.generativeai as genai
import PIL.Image
from dotenv import load_dotenv
load_dotenv(override=True)
import os
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
print(GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

img = PIL.Image.open('screenshot_temp.png')
# Bạn có thể đưa prompt tùy ý để trích xuất dữ liệu
response = model.generate_content(["""
                                   From the image, extract company names and positions that are currently the user working on until present.
                                   Response by giving 2 seperated lists, one for company names and one for positions. Format the list of postions with 'from'
                                   Here's the example format: [<company1>, <company2>,..etc]|[<position1> from <company1>, <position2> from <company1>, <position1> from <company2>, <position2> from <company2>,..etc]
                                   Response only with the lists, no additional text.
                                   """, img])
a = str(response.text)
print(a)
# # a = "[Arkweaver, Various Startups]|[CEO and Co-Founder, Fractional Leadership for AI Companies]"
# com_list = a.split('|')[0]
# pos_list = a.split('|')[1]
# com_list = com_list.strip('[]').split(',')
# pos_list = pos_list.strip('[]').split(',')
# coms = ','.join(com_list)
# poss = ','.join(pos_list)
# print(f'company: {coms}, position: {poss}')
