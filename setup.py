from dotenv import dotenv_values

from utils.database_utils import create_database
from utils.BAG_create_table import main as create_BAG_table
from utils.BAG_load import main as load_BAG

from utils.RVO_Warmtenetten_create_table import main as create_rvo_warmtenetten_table
from utils.RVO_Warmtenetten_download import main as download_rvo_warmtenetten_data
from utils.RVO_Warmtenetten_load import main as load_rvo_warmtenetten

from utils.EP_Online_create_table import main as create_energy_labels_table
from utils.EP_Online_download import main as download_energy_labels_data
from utils.EP_Online_load import load_energy_labels_data

from utils.CBS_load_tables import main as cbs

from utils.CBS_PC6_2019_energy_use_create_table import main as create_CBS_PC6_2019_energy_use_table
from utils.CBS_PC6_2019_energy_use_load import main as load_CBS_PC6_2019_energy_use

def bag():
	print('Creating table for BAG...')
	create_BAG_table()
	print('Done.\n')

	print('Loading the data into Postgres...')
	load_BAG()
	print('Done.\n')

def CBS_PC6():
	print('Creating table for BAG...')
	create_CBS_PC6_2019_energy_use_table()
	print('Done.\n')

	print('Loading the data into Postgres...')
	load_CBS_PC6_2019_energy_use()
	print('Done.\n')

def rvo_warmtenetten():
	print('Creating table for RVO Warmtenetten...')
	create_rvo_warmtenetten_table()
	print('Done.\n')

	print('Downloading the RVO Warmtenetten...')
	download_rvo_warmtenetten_data()
	print('Done.\n')

	print('Loading the data into Postgres...')
	load_rvo_warmtenetten()
	print('Done.\n')

def energy_labels():

	print('Creating table for energy labels...')
	create_energy_labels_table()
	print('Done.\n')

	print('Downloading the EP-Online database...')
	download_energy_labels_data()
	print('Done.\n')

	print('Loading the data into Postgres...')
	load_energy_labels_data()
	print('Done.\n')

def main():

	print('Running setup, this will take time + internet + space...\n')

	env = dotenv_values(".env")
	if len(env) > 0:
		print('CHECK: .env created.\n')
	else:
		print('You need to create an .env file and populate it with the desired information. Check .env.template for an example.')
		print('Aborting.')
		return
		'''
	print('Creating database...')
	create_database()
	print('Done.\n')

	print('====== BAG ======')
	bag()

	print('====== RVO Warmtenetten ======')
	rvo_warmtenetten()

	print('====== Energy labels (EP-Online) ======')
	energy_labels()

	print('====== CBS ======')
	cbs()
	'''
	print('====== CBS Energy Use ======')
	CBS_PC6()
	print('Finished with the setup.')

if __name__ == "__main__":
	main()
