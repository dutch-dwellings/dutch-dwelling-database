from psycopg2.errors import DuplicateObject
import requests

from utils.database_utils import create_database, add_index, make_primary_key, rename_column, delete_column, execute, get_column_type

from utils.BAG_create_table import main as create_BAG_table
from utils.BAG_load import main as load_BAG

from utils.RVO_Warmtenetten_create_table import main as create_rvo_warmtenetten_table
from utils.RVO_Warmtenetten_download import main as download_rvo_warmtenetten_data
from utils.RVO_Warmtenetten_load import main as load_rvo_warmtenetten

from utils.EP_Online_create_table import main as create_energy_labels_table
from utils.EP_Online_download import main as download_energy_labels_data
from utils.EP_Online_load import main as load_energy_labels_data

from utils.CBS_utils import load_cbs_table
from utils.CBS_PC6_2019_energy_use_create_table import main as create_CBS_PC6_2019_energy_use_table
from utils.CBS_PC6_2019_energy_use_download import main as download_CBS_PC6_2019_energy_use
from utils.CBS_PC6_2019_energy_use_load import main as load_CBS_PC6_2019_energy_use

from utils.CBS_PC6_2017_kerncijfers_create_table import main as create_CBS_PC6_2017_kerncijfers_table
from utils.CBS_PC6_2017_kerncijfers_download import main as download_CBS_PC6_2017_kerncijfers
from utils.CBS_PC6_2017_kerncijfers_load import main as load_CBS_PC6_2017_kerncijfers

from utils.elec_consumption_hh_create_table import main as create_elec_consumption_households_table
from utils.elec_consumption_hh_load import main as load_elec_consumption_households

from utils.WoON_load import main as load_WoON

def bag():
	print('Creating table for BAG...')
	create_BAG_table()

	print('Loading the data into Postgres...')
	load_BAG()

	print('Creating indexes...')
	add_index('bag', 'pc6')
	add_index('bag', 'pand_id')
	add_index('bag', 'buurt_id')

def CBS_PC6():
	print('Creating table for CBS PC6...')
	create_CBS_PC6_2019_energy_use_table()

	print('Downloading data...')
	download_CBS_PC6_2019_energy_use()

	print('Loading the data into Postgres...')
	load_CBS_PC6_2019_energy_use()

	print('Creating indexes...')
	add_index('cbs_pc6_2019_energy_use', 'pc6')

def CBS_kerncijfers():
	print('Creating table for CBS PC6...')
	create_CBS_PC6_2017_kerncijfers_table()

	print('Downloading data...')
	download_CBS_PC6_2017_kerncijfers()

	print('Loading the data into Postgres...')
	load_CBS_PC6_2017_kerncijfers()

	print('Creating indexes...')
	add_index('cbs_pc6_2017_kerncijfers', 'pc6')

def create_types():
	print('Adding new Postgres types...')

	print("Creating type 'energy_label_class'...")
	create_energy_label_class_statement = '''
	CREATE TYPE energy_label_class
	AS ENUM
	('G', 'F', 'E', 'D', 'C', 'B', 'A', 'A+', 'A++', 'A+++', 'A++++', 'A+++++')
	'''
	try:
		execute(create_energy_label_class_statement)
	except DuplicateObject:
		print("\tType 'energy_label_class' already exists.")

	print("Creating type 'energy_label_class_range'...")
	create_energy_label_class_range_statement = '''
	CREATE TYPE energy_label_class_range
	AS RANGE (subtype=energy_label_class)
	'''
	try:
		execute(create_energy_label_class_range_statement)
	except DuplicateObject:
		print("\tType 'energy_label_class_range' already exists.")

def rvo_warmtenetten():
	print('Creating table for RVO Warmtenetten...')
	create_rvo_warmtenetten_table()

	print('Downloading the RVO Warmtenetten...')
	download_rvo_warmtenetten_data()

	print('Loading the data into Postgres...')
	load_rvo_warmtenetten()

	print('Creating indexes...')
	add_index('rvo_warmtenetten', 'buurt_code')

def energy_labels():

	print('Creating table for energy labels...')
	create_energy_labels_table()

	print('Downloading the EP-Online database...')
	try:
		download_energy_labels_data()
	except requests.exceptions.ConnectionError as e:
		print(f'\tERROR! Could not download EP-Online due to a ConnectionError. Are you connected to the internet? Error:\n\t{e}')
		# do not process any further
		return
	except ConnectionError as e:
		print(f'\tERROR! Could not download EP-Online due to a ConnectionError. Error:\n\t{e}')
		# do not process any further
		return

	print('Loading the data into Postgres...')
	load_energy_labels_data()

	print('Deleting columns...')
	# is always NULL
	delete_column('energy_labels', 'bagstandplaatsid')
	# is only relevant for 'U' buildings
	delete_column('energy_labels', 'sbicode')

	print('Creating indexes...')
	add_index('energy_labels', 'vbo_id')
	add_index('energy_labels', 'pand_id')
	add_index('energy_labels', 'pc6')

def cbs():
	# Include a tuple with (table_id, typed_data_set),
	# with the second value indicating whether you want the
	# table to not 'expand' IDs (such as Buurten en Wijken, this
	# can be helpful when you need the raw buurt_id)
	cbs_tables = [
		# Energieverbruik particuliere woningen; woningtype, wijken en buurten, 2018
		# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=84585NED&_theme=279
		("84585NED", False),
		# Woningen; hoofdverwarmings; buurt 2019
		# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=84983NED&_theme=126
		("84983NED", True),
		# Kerncijfers wijken en buurten 2020
		# https://opendata.cbs.nl/portal.html?_la=nl&_catalog=CBS&tableId=84799NED&_theme=235
		("84799NED", False),
		# Kerncijfers wijken en buurten 2019
		# https://opendata.cbs.nl/portal.html?_la=nl&_catalog=CBS&tableId=84583NED&_theme=235
		("84583NED", False),
		# Woonplaatsen in Nederland 2020
		# https://www.cbs.nl/nl-nl/cijfers/detail/84734NED
		("84734NED", False),
		# Elektriciteitslevering vanuit het openbare net; woningkenmerken, bewoners
		# https://opendata.cbs.nl/#/CBS/nl/dataset/83882NED/table?ts=1622540319896
		("83882NED", False),
		# Aardgaslevering vanuit het openbare net; woningkenmerken
		# https://opendata.cbs.nl/#/CBS/nl/dataset/83878NED/table
		("83878NED", False)
	]
	for table in cbs_tables:
		load_cbs_table(table[0], typed_data_set=table[1])

	print('Renaming columns...')
	column_renames = [
		# Format: (table_name, col_name, new_col_name)
		('cbs_84799ned_kerncijfers_wijken_en_buurten_2020', 'codering', 'area_code'),
		('cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed', 'wijken_en_buurten', 'area_code')
	]
	for rename in column_renames:
		rename_column(*rename)

	print('Creating indexes...')
	indexes = [
		('cbs_84799ned_kerncijfers_wijken_en_buurten_2020', 'area_code'),
		('cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed', 'area_code')
	]
	for index in indexes:
		add_index(*index)

	print('Transforming data...')
	col_type = get_column_type('cbs_83878ned_aardgaslevering_woningkenmerken', 'energielabelklasse')
	if col_type != 'energy_label_class':

		delete_statement = '''
		DELETE FROM cbs_83878ned_aardgaslevering_woningkenmerken
		WHERE energielabelklasse = 'Totaal'
		'''

		change_to_null_statement = '''
		UPDATE cbs_83878ned_aardgaslevering_woningkenmerken
		SET energielabelklasse = NULL
		WHERE energielabelklasse = 'Geen label'
		'''

		alter_type_statement = '''
		ALTER TABLE cbs_83878ned_aardgaslevering_woningkenmerken
		ALTER COLUMN energielabelklasse
		TYPE energy_label_class
		USING LEFT(energielabelklasse, 1)::energy_label_class
		'''

		execute(delete_statement)
		execute(change_to_null_statement)
		execute(alter_type_statement)

def main():

	print('Starting setup, this will take time + internet + space.\n')

	print('Creating database...')
	create_database()

	print('\nCreating types...')
	create_types()

	print('\n====== BAG ======')
	bag()

	print('\n====== RVO Warmtenetten ======')
	rvo_warmtenetten()

	print('\n====== Energy labels (EP-Online) ======')
	energy_labels()

	print('\n====== CBS ======')
	cbs()

	print('\n====== CBS Energy Use ======')
	CBS_PC6()

	print('\n====== CBS Demographics ======')
	CBS_kerncijfers()

	print('\n====== WoON ======')
	load_WoON()

	print('\nFinished with the setup.')

if __name__ == "__main__":
	main()
