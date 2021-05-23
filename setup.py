from dotenv import dotenv_values

from utils.database_utils import create_database
from utils.EP_Online_create_table import create_energy_labels_table
from utils.EP_Online_download import main as download_energy_labels_data
from utils.EP_Online_load import load_energy_labels_data

def main():

	print('Running setup, this will take time + internet + space...\n')

	env = dotenv_values(".env")
	if len(env) > 0:
		print('CHECK: .env created.\n')
	else:
		print('You need to create an .env file and populate it with the desired information. Check .env.template for an example.')
		print('Aborting.')
		return

	print('Creating database...')
	create_database()
	print('Done.\n')

	print('Creating table...')
	create_energy_labels_table()
	print('Done.\n')

	print('Downloading the EP-Online database...')
	download_energy_labels_data()
	print('Done.\n')

	print('Loading the data into Postgres...')
	load_energy_labels_data()
	print('Done.\n')

	print('Finished with the setup.')

if __name__ == "__main__":
	main()
