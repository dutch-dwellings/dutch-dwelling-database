import os
import re

import requests
from dotenv import dotenv_values

from utils import prefix_path, data_dir, save_to_file,unzip


env = dotenv_values(".env")
API_KEY = env['EP_ONLINE_API_KEY']

URL = "https://www.ep-online.nl/ep-online/PublicData"

VALIDATION_URL = f"{URL}/ValidateAsync"
DOWNLOAD_URL = f"{URL}/Download"

def get_request_parameters():

	# we use a session so we can share the session cookie between requests
	s = requests.Session()

	r = s.get(URL)

	# extract the RequestVerificationToken necessary for validating the API key
	RVT_pattern = re.compile('"__RequestVerificationToken" type="hidden" value="(.*)" />')
	RequestVerificationToken = re.search(RVT_pattern, r.text).group(1)

	# get the mutationfile-id for the second entry, which is (we expect at least) the entry for the CSV file:
	id_pattern = re.compile('data-mutationfile-id="([0-9]*)"')
	csv_id = re.findall(id_pattern, r.text)[1]

	# validate the API key
	r = s.post(VALIDATION_URL, data={"__RequestVerificationToken": RequestVerificationToken, "ApiKey": API_KEY})

	# extract the new RequestVerificationToken
	html = r.json()['mutationFilesHtml']
	RequestVerificationToken2 = re.search(RVT_pattern, html).group(1)

	session_cookies = s.cookies.get_dict()

	return csv_id, RequestVerificationToken2, session_cookies

def main():

	csv_id, RequestVerificationToken, cookies = get_request_parameters()

	filename = 'v20210501_csv.zip'
	prefix = 'EP-Online_'
	prefixed_filename = prefix_path(filename, prefix)
	path = os.path.join(data_dir, prefixed_filename)

	save_to_file(DOWNLOAD_URL, path, method="POST", data={"__RequestVerificationToken":RequestVerificationToken, "ApiKey": API_KEY, "id": csv_id}, cookies=cookies, expected_size='80MB')

	unzip(path, expected_size='3860MB', prefix=prefix)

if __name__ == "__main__":
	main()

# TODO:
# - automatically get the filename (need to parse html probably)
# - automatically get filesize
