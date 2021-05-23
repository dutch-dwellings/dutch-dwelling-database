from dotenv import dotenv_values
import requests

env = dotenv_values(".env")

EP_ONLINE_API_ENDPOINT = "https://public.ep-online.nl/api/v2/"
EP_ONLINE_API_PANDENERGIELABEL = EP_ONLINE_API_ENDPOINT + 'PandEnergielabel/AdresseerbaarObject/'

def main():

	test_id = "0503010000070044"

	url = EP_ONLINE_API_PANDENERGIELABEL + test_id

	r = requests.get(url, headers={'Authorization': env['EP_ONLINE_API_KEY']})
	print(r.text)

if __name__ == "__main__":
	main()
