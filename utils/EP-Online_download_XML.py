import os

from dotenv import dotenv_values
import requests

from utils import save_to_file, unzip, prefix_path


env = dotenv_values(".env")

# EP-Online:
# - API documentation: https://public.ep-online.nl/swagger/index.html
# - response file documentation: https://www.rvo.nl/sites/default/files/2021/01/handleiding-ep-online-opvragen-van-bestanden-en-webservice-januari-2021.pdf
EP_ONLINE_API_ENDPOINT = "https://public.ep-online.nl/api/v1/"
EP_ONLINE_API_MUTATIONFILE = EP_ONLINE_API_ENDPOINT + "Mutatiebestand/DownloadInfo"
EP_ONLINE_API_PING = EP_ONLINE_API_ENDPOINT + "Ping"

class AuthenticationError(Exception):
	pass
class ConfirmationError(Exception):
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

	prefix = 'EP-Online_'
	prefixed_filename = f'{prefix}{filename}'
	project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
	path = os.path.join(project_dir, 'data', prefixed_filename)

	save_to_file(downloadUrl, path, expected_size='120MB')

	unzip(path, expected_size='3860MB', prefix=prefix)

if __name__ == "__main__":
	main()

# TODO:
# - try to download the smaller CSV file (880MB) instead of the XML file (3860MB)
# - consider deleting the ZIP file after unzipping (but might be useful to prevent re-downloading)
# - give a warning before unzipping the file that it can take quite a lot of disk scape
