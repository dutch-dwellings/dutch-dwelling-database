import os
import sys

from dotenv import dotenv_values
import requests

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from file_utils import prefix_path, data_dir, save_to_file, unzip


env = dotenv_values(".env")

# EP-Online:
# - API documentation: https://public.ep-online.nl/swagger/index.html
# - response file documentation: https://www.rvo.nl/sites/default/files/2021/01/handleiding-ep-online-opvragen-van-bestanden-en-webservice-januari-2021.pdf
EP_ONLINE_API_ENDPOINT = "https://public.ep-online.nl/api/v2/"
EP_ONLINE_API_MUTATIONFILE = EP_ONLINE_API_ENDPOINT + "Mutatiebestand/DownloadInfo"

class AuthenticationError(Exception):
	pass


def handle_request(r):
	if r.status_code == 200:
		filename = r.json()['bestandsnaam']
		downloadUrl = r.json()['downloadUrl']
		return filename, downloadUrl
	elif r.status_code == 401:
		raise AuthenticationError(f"Status 401: Not authenticated for the EP-Online API. Check the EP_ONLINE_API_KEY in .env. API-key used: {env['EP_ONLINE_API_KEY']}.")
	else:
		raise Exception(f'Unexpected error trying to connect to EP-Online API. Status code: {r.status_code}.')

def main():

	r = requests.get(EP_ONLINE_API_MUTATIONFILE, headers={'Authorization': env['EP_ONLINE_API_KEY']})
	filename, downloadUrl = handle_request(r)

	prefix = 'EP_Online_'
	prefixed_filename = prefix_path(filename, prefix)
	path = os.path.join(data_dir, prefixed_filename)

	save_to_file(downloadUrl, path, expected_size='120MB')

	unzip(path, expected_size='3860MB', prefix=prefix)

if __name__ == "__main__":
	main()


