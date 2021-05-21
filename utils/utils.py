import os
from zipfile import ZipFile

def save_to_file(url, path, expected_size=None):
	'''
	Download the file at 'url' and save it at 'path'.
	Warn and ask confirmation for downloading when
	the 'expected_size' of the download has been set
	(as a string).
	'''

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
	'''
	Unzip the file at 'path'. Warn and ask for
	confirmation before unzipping if the string
	'expected_size' of the unzipped file has been set.
	Rename the unzipped file with a 'prefix' if specified.
	'''

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
