import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from file_utils import data_dir, save_to_file, unzip

# info: https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/gegevens-per-postcode
URL = 'https://download.cbs.nl/postcode/CBS-PC6-2017-v3.zip'
FILENAME = 'CBS_PC6_2017_v3.zip'

def main():

	path = os.path.join(data_dir, FILENAME)

	save_to_file(URL, path, expected_size='274MB')
	unzip(path, files=['CBS_PC6_2017_v3.csv'], expected_size='302MB')

if __name__ == '__main__':
	main()
