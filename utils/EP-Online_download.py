import os
from zipfile import ZipFile

from dotenv import dotenv_values
import requests


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


def save_to_file(url, path, expected_size=None):

	filename = os.path.basename(path)

	if os.path.isfile(path):
		confirmation = input(f'File {filename} already exists, do you want to redownload it? (y/n)\n')
		if confirmation.lower() != 'y':
			# skip download, still go on with the rest of processing
			return

	if expected_size:
		confirmation = input(f'Preparing download of {filename}, expected size {expected_size}... do you want to continue? (y/n)\n')
		if confirmation.lower() != 'y':
			raise ConfirmationError('Aborting program on users request')

	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "wb") as file:
		print('Starting download...')
		response = requests.get(url)
		print('finished download.')
		file.write(response.content)


def unzip(path, expected_size=None, prefix=None):

	with ZipFile(path, 'r') as zip_ref:
		filename = zip_ref.namelist()[0]

		unzipped_path = os.path.join(os.path.dirname(path), filename)
		prefixed_path = prefix_path(unzipped_path, prefix)

		if os.path.exists(unzipped_path) or os.path.exists(prefixed_path):
			confirmation = input(f'File has already been unzipped at either {unzipped_path} or {prefixed_path}. Do you want to redo unzipping? (y/n)\n')
			if confirmation.lower() != 'y':
				return

		print('Starting unzipping...')
		zip_ref.extractall(os.path.dirname(path))
		print('finished unzipping.')

	os.rename(unzipped_path, prefixed_path)


def prefix_path(path, prefix):
	# allow prefix=None
	if prefix:
		filename = os.path.basename(path)
		dirname = os.path.dirname(path)
		return os.path.join(dirname, f'{prefix}{filename}')
	else:
		return path

def main():

	r = requests.get(EP_ONLINE_API_MUTATIONFILE, headers={'Authorization': env['EP_ONLINE_API_KEY']})
	filename, downloadUrl = handle_request(r)

	print(downloadUrl)
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
