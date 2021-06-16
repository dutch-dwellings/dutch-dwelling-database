import os
from zipfile import ZipFile

from dotenv import dotenv_values
import requests


class ConfirmationError(Exception):
	pass

def save_to_file(url, path, expected_size=None, method='GET', data={}, cookies={}):
	'''
	Download the file at 'url' and save it at 'path'.
	Will not redownload when file already exists.
	'''

	filename = os.path.basename(path)

	if os.path.isfile(path):
		print(f'File already exists at {path}, skipping download')
		return

	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "wb") as file:
		print(f'Starting download... (expected size: {expected_size})')
		if method == 'GET':
			response = requests.get(url)
		elif method == 'POST':
			response = requests.post(url, data=data, cookies=cookies)
		else:
			raise ValueError(f'Unexpected method {method}, try GET or POST')
		file.write(response.content)


def unzip(path, expected_size=None, prefix=None, files=None):
	'''
	Unzip the archive at 'path'. Only zip the files specified in
	'files' (default: extract all files).
	Rename the unzipped files with a 'prefix' if specified.
	Will not unzip file when a file already exists at the target location.
	'''

	with ZipFile(path, 'r') as zip_ref:
		if files == None:
			files = zip_ref.namelist()

		for filename in files:
			unzipped_path = os.path.join(os.path.dirname(path), filename)
			prefixed_path = prefix_path(unzipped_path, prefix)

			if os.path.exists(prefixed_path):
				print(f'File has already been unzipped at {prefixed_path}')
			else:
				print(f'Unzipping {filename} from {path}')
				zip_ref.extract(filename, path=os.path.dirname(path))
				os.rename(unzipped_path, prefixed_path)

def prefix_path(path, prefix):
	'''
	Prefix the file at 'path' with 'prefix'
	(may be None)
	'''

	# allow prefix=None
	if prefix:
		filename = os.path.basename(path)
		dirname = os.path.dirname(path)
		return os.path.join(dirname, f'{prefix}{filename}')
	else:
		return path

def get_env():
	env_path = os.path.join(project_dir, '.env')
	if os.path.exists(env_path):
		return dotenv_values(env_path)
	else:
		raise FileNotFoundError(f'Expected .env file at {env_path} but file does not exist. Please populate it by taking .env.bak as an example.')

project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
data_dir = os.path.join(project_dir, 'data')
