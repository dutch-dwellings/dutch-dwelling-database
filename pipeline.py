import time

from psycopg2 import sql
from psycopg2.extras import DictCursor

from utils.database_utils import get_connection, get_bag_sample, get_neighbourhoods_sample, get_neighbourhoods_sample_UAE
from utils.create_results_table import main as create_results_table

from modules.classes import Dwelling

from modules.regions_module import RegionsModule
from modules.energy_label_module import EnergyLabelModule, EnergyLabelRegionalModule
from modules.gas_consumption_comparison_module import GasConsumptionComparisonModule, GasConsumptionComparisonRegionalModule
from modules.electricity_consumption_comparison_module import ElectricityConsumptionComparisonModule, ElectricityConsumptionComparisonRegionalModule

from modules.district_space_heating_module import DistrictSpaceHeatingModule, DistrictSpaceHeatingRegionalModule
from modules.gas_space_heating_module import GasSpaceHeatingModule, GasSpaceHeatingRegionalModule
from modules.electric_space_heating_module import ElectricSpaceHeatingModule, ElectricSpaceHeatingRegionalModule

from modules.gas_water_heating_module import GasWaterHeatingModule
from modules.electric_water_heating_module import ElectricWaterHeatingModule
from modules.district_water_heating_module import DistrictWaterHeatingModule

from modules.gas_cooking_module import GasCookingModule
from modules.electric_cooking_module import ElectricCookingModule

from modules.sampling_module import SamplingModule


def main():

	start_time = time.time()
	i = 0

	connection = get_connection()

	cursor = connection.cursor()

	dwellings_count_query = "SELECT COUNT(vbo_id) FROM bag"
	cursor.execute(dwellings_count_query)
	dwelling_count = cursor.fetchone()[0]
	cursor.close()


	# Also deletes existing `results' table
	print("Creating table 'results'...")
	create_results_table()

	# print("Getting a BAG sample...")
	# sample = get_bag_sample(connection, 1000)
	# sample = get_neighbourhoods_sample_UAE(connection)
	# sample = get_neighbourhoods_sample(connection, 'BU034405%', 100000000)

	print("Initiating modules...")

	RegionalModules = [
		EnergyLabelRegionalModule,
		GasConsumptionComparisonRegionalModule,
		ElectricityConsumptionComparisonRegionalModule,
		DistrictSpaceHeatingRegionalModule,
		GasSpaceHeatingRegionalModule,
		ElectricSpaceHeatingRegionalModule
	]
	regional_modules = [RegionalModule(connection) for RegionalModule in RegionalModules]

	Modules = [
		# Create neccesary dwelling attributes.
		# RegionsModule should not be confused with a 'RegionalModule':
		# RegionsModule adds regions, works on dwellings;
		# a RegionalModule works on regions.
		RegionsModule,
		EnergyLabelModule,
		GasConsumptionComparisonModule,
		ElectricityConsumptionComparisonModule,
		# Space heating
		DistrictSpaceHeatingModule,
		GasSpaceHeatingModule,
		ElectricSpaceHeatingModule,
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

	# Optional variables that only some modules require.
	kwargs = {
		'regional_modules': regional_modules
	}

	modules = [Module(connection, **kwargs) for Module in Modules]

	# Querying BAG
	cursor = connection.cursor(cursor_factory=DictCursor)
	query = "SELECT * FROM bag ORDER BY buurt_id"
	cursor.execute(query)
	sample = cursor.fetchmany(100000)
	sample = cursor.fetchmany(100000)
	sample = cursor.fetchmany(100000)
	sample = cursor.fetchmany(80000)
	while i < dwelling_count:
		print("Getting a BAG sample...")
		sample = cursor.fetchmany(100000)

		print("Processing entries...")
		for entry in sample:
			dwelling = Dwelling(dict(entry), connection)

			for module in modules:
				module.process(dwelling)

			dwelling.save()
			i += 1
			if i % 100 == 0:
				print(f'   processed dwelling: {i}', end='\r')

	print("\nCommiting and closing...")
	cursor.close()
	connection.commit()
	connection.close()

	print(f'Processed {i:,} records in {(time.time() - start_time):.2f} seconds.')


if __name__ == "__main__":
	main()
