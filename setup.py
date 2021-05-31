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

from utils.CBS_utils import load_cbs_table

def bag():
	print('Creating table for BAG...')
	create_BAG_table()
	print('Done.\n')

	print('Loading the data into Postgres...')
	load_BAG()
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

def cbs():
	cbs_tables = [
		# Energieverbruik particuliere woningen; woningtype, wijken en buurten, 2018
		# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=84585NED&_theme=279
		"84585NED"
	]
	for table in cbs_tables:
		load_cbs_table(table)

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

	print('====== BAG ======')
	bag()

	print('====== RVO Warmtenetten ======')
	rvo_warmtenetten()

	print('====== Energy labels (EP-Online) ======')
	energy_labels()

	print('====== CBS ======')
	cbs()

	print('Finished with the setup.')

if __name__ == "__main__":
	main()
