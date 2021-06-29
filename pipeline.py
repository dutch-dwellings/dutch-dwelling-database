import time
import pandas as pd

from psycopg2 import sql
from psycopg2.extras import DictCursor

from utils.database_utils import get_connection, get_bag_sample, get_neighbourhoods_sample, get_neighbourhoods_sample_UAE
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

def main():

	start_time = time.time()

	connection = get_connection()

	# Also deletes existing `results' table
	print("Creating table 'results'...")
	create_results_table()

	print("Initiating modules...")
	regional_modules = get_regional_modules(connection)
	modules = get_modules(connection, regional_modules)

	print("Getting dwellings...")
	cursor = connection.cursor()
	query = '''
		SELECT
			vbo_id, pc6, oppervlakte, bouwjaar, woningtype, buurt_id
		FROM
			bag
		ORDER BY
			buurt_id
		LIMIT
			10000
	'''
	cursor.execute(query)

	print('Starting processing...')
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

		# Memory cleanup unused regions
		if all(isinstance(dwellings, Dwelling) for dwellings in dwelling.regions['pc6'].dwellings) is True:
			del dwelling.regions['pc6']
		if all(isinstance(dwellings, Dwelling) for dwellings in dwelling.regions['buurt'].dwellings) is True:
			del dwelling.regions['buurt']
		del dwelling

		i += 1
		if i % 100 == 0:
			print(f'   processed dwelling: {i}', end='\r')
		if i % 10000 == 0:
			connection.commit()

	print("\nCommiting and closing...")
	cursor.close()
	connection.commit()
	connection.close()

	print(f'Processed {i:,} records in {(time.time() - start_time):.2f} seconds.')

if __name__ == "__main__":
	main()
