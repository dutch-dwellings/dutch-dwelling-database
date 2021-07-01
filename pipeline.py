import sys
import time

from psycopg2 import sql
from psycopg2.extras import DictCursor

from utils.database_utils import get_connection, make_primary_key
from utils.create_results_table import main as create_results_table

from modules.classes import Dwelling, PlaceholderDwelling

from modules.base_bag_data_module import BaseBagDataModule

from modules.regions_module import RegionsModule
from modules.energy_label_module import EnergyLabelModule, EnergyLabelPredictionModule, EnergyLabelRegionalModule
from modules.gas_consumption_comparison_module import GasConsumptionComparisonModule, GasConsumptionComparisonRegionalModule
from modules.electricity_consumption_comparison_module import ElectricityConsumptionComparisonModule, ElectricityConsumptionComparisonRegionalModule

from modules.district_space_heating_module import DistrictSpaceHeatingModule, DistrictSpaceHeatingRegionalModule
from modules.gas_space_heating_module import GasSpaceHeatingModule, GasSpaceHeatingRegionalModule
from modules.electric_space_heating_module import ElectricSpaceHeatingModule, ElectricSpaceHeatingRegionalModule

from modules.insulation_module import InsulationModule

from modules.gas_water_heating_module import GasWaterHeatingModule
from modules.electric_water_heating_module import ElectricWaterHeatingModule
from modules.district_water_heating_module import DistrictWaterHeatingModule

from modules.gas_cooking_module import GasCookingModule
from modules.electric_cooking_module import ElectricCookingModule

from modules.sampling_module import SamplingModule


# Modules that will run on the Regions.
RegionalModules = [
	EnergyLabelRegionalModule,
	GasConsumptionComparisonRegionalModule,
	ElectricityConsumptionComparisonRegionalModule,
	DistrictSpaceHeatingRegionalModule,
	GasSpaceHeatingRegionalModule,
	ElectricSpaceHeatingRegionalModule
]

# Modules that will run on PlaceholderDwellings
# when instantiating a region. Specify only those
# that are required for the RegionalModules to do
# their job.
PC6DwellingModules = []
BuurtDwellingModules = [
	EnergyLabelModule,
	BaseBagDataModule
]

Modules = [
	# Create neccesary dwelling attributes.
	# RegionsModule should not be confused with a 'RegionalModule':
	# RegionsModule adds regions, works on dwellings;
	# a RegionalModule works on regions.
	RegionsModule,
	EnergyLabelModule,
	EnergyLabelPredictionModule,
	GasConsumptionComparisonModule,
	ElectricityConsumptionComparisonModule,
	# Space heating
	DistrictSpaceHeatingModule,
	GasSpaceHeatingModule,
	ElectricSpaceHeatingModule,
	InsulationModule,
	# Water heating
	DistrictWaterHeatingModule,
	GasWaterHeatingModule,
	ElectricWaterHeatingModule,
	# Cooking
	GasCookingModule,
	ElectricCookingModule,
	# Sampling
	SamplingModule
]

def get_regional_modules(connection):
	return [RegionalModule(connection) for RegionalModule in RegionalModules]

def get_modules(connection, regional_modules):
	# Optional variables that only some modules require.
	kwargs = {
		'regional_modules': regional_modules,
		'pc6_dwelling_modules': [Module(connection) for Module in PC6DwellingModules],
		'buurt_dwelling_modules': [Module(connection) for Module in BuurtDwellingModules]
	}
	return [Module(connection, **kwargs) for Module in Modules]

def get_rowcount_estimate(table_name, connection):
	# adapted from https://stackoverflow.com/a/2611745/7770056
	rowcount_estimate_query = '''
	SELECT
		reltuples::int
	FROM
		pg_class
	WHERE
		relname=%s
	'''
	cursor = connection.cursor()
	cursor.execute(rowcount_estimate_query, (table_name,))
	(result,) = cursor.fetchone()
	cursor.close()
	return result

def pipeline(query, connection, fresh=False, N=None):
	# set N = None to process full BAG.
	# set fresh = True to delete previous results.

	start_time = time.time()

	print(f'fresh: {fresh} (if True, previous results will be deleted)')

	# Also deletes existing `results' table
	print("\nCreating table 'results'...")
	create_results_table(fresh)

	print("Adding primary key on vbo_id...")
	make_primary_key('results', 'vbo_id')

	print("\nInitiating modules...")
	regional_modules = get_regional_modules(connection)
	modules = get_modules(connection, regional_modules)

	print("\nGetting dwellings...")
	# We create a named server-side cursor:
	# https://www.psycopg.org/docs/usage.html#server-side-cursors
	# This keeps the memory usage down
	# since it will only fetch about 2000 (see cursor.itersize)
	# rows at a time into the Python memory.
	# You don't need to close() this cursor afterwards (in fact
	# the cursor disappears after a commit).
	cursor = connection.cursor(name='pipeline-cursor')
	cursor.execute(query)

	# import pdb
	# pdb.set_trace()

	bag_count = 7892928
	results_count_estimate = get_rowcount_estimate('results', connection)

	print(f'Batch statistics:')
	print(f'   BAG entries: {bag_count}')
	print(f'   estimate of current number of results (might be outdated): {results_count_estimate} ({results_count_estimate/bag_count*100:.2f}%)')
	print(f'   this batch: {"no number specified" if N is None else N}')

	print('\nStarting processing...')

	i = 0
	for (vbo_id, pc6, oppervlakte, bouwjaar, woningtype, buurt_id) in cursor:

		attributes = {
			'vbo_id': vbo_id,
			'pc6': pc6,
			'oppervlakte': oppervlakte,
			'bouwjaar': bouwjaar,
			'woningtype': woningtype,
			'buurt_id': buurt_id
		}

		dwelling = Dwelling(attributes, connection)

		for module in modules:
			module.process(dwelling)
		dwelling.save()

		i += 1
		if i % 100 == 0:
			print(f'   processed dwelling: {i}', end='\r')

		if i == N:
			break

	print("\n\nCommiting and closing...")
	connection.commit()
	connection.close()

	print(f'Processed {i:,} records in {(time.time() - start_time):.2f} seconds.')

def main(*args):
	'''
	Options:
		--fresh: delete previous results
		--vbo_id {vbo_id}: process only the dwellings in the
		same buurt as 'vbo_id'
		--N {N}: limit pipeline to N dwellings (won't work
		if --vbo_id also specified)
	'''

	print("\n=== DUTCH DWELLINGS PIPELINE ===\n")

	# Makes the pipeline both callable from
	# CLI and from other script.
	if len(args) == 0:
		args = sys.argv

	connection = get_connection()

	# Determines whether to delete existing results
	if '--fresh' in args:
		fresh = True
	else:
		fresh = False

	# If you specify a vbo_id, we will get all the dwellings
	# in the neighbourhood.
	if '--vbo_id' in args:
		index = args.index('--vbo_id')
		vbo_id = args[index + 1]
		print('processing buurt for one vbo')
		print(f'   vbo_id: {vbo_id}')
		buurt_id_query = '''
		SELECT buurt_id
		FROM bag
		WHERE vbo_id = %s
		'''
		cursor = connection.cursor()
		cursor.execute(buurt_id_query, (vbo_id,))
		(buurt_id,) = cursor.fetchone()

		print(f'   buurt_id: {buurt_id}')

		query = '''
			SELECT
				vbo_id, pc6, oppervlakte, bouwjaar, woningtype, buurt_id
			FROM
				bag
			WHERE
				buurt_id = %s
				AND
				NOT EXISTS
				(SELECT vbo_id
				FROM results
				WHERE results.vbo_id = bag.vbo_id
				)
		'''
		query = cursor.mogrify(query, (buurt_id,))
		N = None

	else:
		query = '''
			SELECT
				vbo_id, pc6, oppervlakte, bouwjaar, woningtype, buurt_id
			FROM
				bag
			WHERE
				NOT EXISTS
				(SELECT vbo_id
				FROM results
				WHERE results.vbo_id = bag.vbo_id
				)
			ORDER BY
				buurt_id
		'''

		if '--N' in args:
			index = args.index('--N')
			N = int(args[index + 1])
		else:
			N = None

	pipeline(query, connection, fresh, N)

if __name__ == "__main__":
	main()
