from utils.database_utils import create_database, add_index

from utils.BAG_create_table import main as create_BAG_table
from utils.BAG_load import main as load_BAG

from utils.RVO_Warmtenetten_create_table import main as create_rvo_warmtenetten_table
from utils.RVO_Warmtenetten_download import main as download_rvo_warmtenetten_data
from utils.RVO_Warmtenetten_load import main as load_rvo_warmtenetten

from utils.EP_Online_create_table import main as create_energy_labels_table
from utils.EP_Online_download import main as download_energy_labels_data
from utils.EP_Online_load import load_energy_labels_data

from utils.CBS_utils import load_cbs_table
from utils.CBS_PC6_2019_energy_use_create_table import main as create_CBS_PC6_2019_energy_use_table
from utils.CBS_PC6_2019_energy_use_load import main as load_CBS_PC6_2019_energy_use

from utils.CBS_PC6_2017_kerncijfers_create_table import main as create_CBS_PC6_2017_kerncijfers_table
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
	add_index('bag', 'postcode')

def CBS_PC6():
	print('Creating table for CBS PC6...')
	create_CBS_PC6_2019_energy_use_table()

	print('Loading the data into Postgres...')
	load_CBS_PC6_2019_energy_use()

def CBS_kerncijfers():
	print('Creating table for CBS PC6...')
	create_CBS_PC6_2017_kerncijfers_table()

	print('Loading the data into Postgres...')
	load_CBS_PC6_2017_kerncijfers()

def elec_consumption_households():
	print('Creating table for CBS PC6...')
	create_elec_consumption_households_table()

	print('Loading the data into Postgres...')
	load_elec_consumption_households()

def rvo_warmtenetten():
	print('Creating table for RVO Warmtenetten...')
	create_rvo_warmtenetten_table()

	print('Downloading the RVO Warmtenetten...')
	download_rvo_warmtenetten_data()

	print('Loading the data into Postgres...')
	load_rvo_warmtenetten()

def energy_labels():

	print('Creating table for energy labels...')
	create_energy_labels_table()

	print('Downloading the EP-Online database...')
	download_energy_labels_data()

	print('Loading the data into Postgres...')
	load_energy_labels_data()

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

def main():

	print('Starting setup, this will take time + internet + space.\n')

	print('Creating database...')
	create_database()

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

	print('\n====== Electricity consumption households ======')
	elec_consumption_households()

	print('\n====== WoON === ===')
	load_WoON()

	print('\nFinished with the setup.')

if __name__ == "__main__":
	main()
