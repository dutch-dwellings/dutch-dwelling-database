import os
import sys

from dotenv import dotenv_values
import requests

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from file_utils import prefix_path, data_dir, save_to_file, unzip


env = dotenv_values(".env")

# RVO:
# Response file documentation: https://rvo-nl.github.io/EnergieWiki/
RVO_WARMTENETTEN_BASE_URL = "https://rvo.b3p.nl/geoserver/WarmteAtlas/wfs?REQUEST=getFeature"
RVO_WARMTENETTEN_TYPENAME = "&typeName=WarmteNetten"
RVO_WARMTENETTEN_OUTPUTFORMAT = "&outputformat=CSV"
RVO_WARMTENETTEN_URL = RVO_WARMTENETTEN_BASE_URL + RVO_WARMTENETTEN_TYPENAME + RVO_WARMTENETTEN_OUTPUTFORMAT

filename = "Download-WarmteNetten-CSV"

def main():

	prefix = 'RVO_Warmtenetten_'
	prefixed_filename = prefix_path(filename, prefix)
	path = os.path.join(data_dir, prefixed_filename)

	save_to_file(RVO_WARMTENETTEN_URL, path, expected_size='7MB')

if __name__ == "__main__":
	main()
