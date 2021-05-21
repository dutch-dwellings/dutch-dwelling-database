import re

import requests
from dotenv import dotenv_values


env = dotenv_values(".env")
API_KEY = env['EP_ONLINE_API_KEY']

URL = "https://www.ep-online.nl/ep-online/PublicData"

VALIDATION_URL = f"{URL}/ValidateAsync"
DOWNLOAD_URL = f"{URL}/Download"

# we use a session so we can share the session cookie between requests
s = requests.Session()

print('Requesting main page...')
r = s.get(URL)

# extract the RequestVerificationToken necessary for validating the API key
RVT_pattern = re.compile('"__RequestVerificationToken" type="hidden" value="(.*)" />')
RequestVerificationToken = re.search(RVT_pattern, r.text).group(1)

# get the mutationfile-id for the second entry, which is (we expect at least) the entry for the CSV file:
id_pattern = re.compile('data-mutationfile-id="([0-9]*)"')
csv_id = re.findall(id_pattern, r.text)[1]

# validate the API key
print('POSTing for validation...')
r = s.post(VALIDATION_URL, data={"__RequestVerificationToken": RequestVerificationToken, "ApiKey": API_KEY})

# extract the new RequestVerificationToken
html = r.json()['mutationFilesHtml']
RequestVerificationToken2 = re.search(RVT_pattern, html).group(1)

# download the CSV
print('POSTing for download...')
r = s.post(DOWNLOAD_URL, data={"__RequestVerificationToken":RequestVerificationToken, "ApiKey": API_KEY, "id": csv_id})

print(f'Done (status: {r.status_code})')

# with open('csv.zip', "wb") as file:
# 	file.write(r.content)
