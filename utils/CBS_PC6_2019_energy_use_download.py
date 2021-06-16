import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from file_utils import data_dir, save_to_file, unzip

# info: https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/gegevens-per-postcode
URL = 'https://www.cbs.nl/-/media/_excel/2020/33/energiecijfers_postcode6.zip'
FILENAME = 'Energiecijfers_postcode6.zip'
PREFIX = 'CBS_PC6_2019_'


def main():

	path = os.path.join(data_dir, PREFIX + FILENAME)

	save_to_file(URL, path, expected_size='3.6MB')
	unzip(path, files=['Publicatiefile_Energie_postcode6_2019.csv'], expected_size='17MB', prefix=PREFIX)

if __name__ == '__main__':
	main()
