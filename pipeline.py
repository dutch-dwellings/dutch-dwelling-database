import time

from psycopg2 import sql

from utils.database_utils import get_connection, get_bag_sample, get_neighbourhoods_sample
from utils.create_results_table import main as create_results_table

from modules.classes import Dwelling

from modules.energy_label_module import EnergyLabelModule
from modules.gas_consumption_comparison_module import GasConsumptionComparisonModule
from modules.electricity_consumption_comparison_module import ElectricityConsumptionComparisonModule

from modules.district_space_heating_module import DistrictSpaceHeatingModule
from modules.gas_space_heating_module import GasSpaceHeatingModule
from modules.electric_space_heating_module import ElectricSpaceHeatingModule

from modules.gas_water_heating_module import GasWaterHeatingModule
from modules.electric_water_heating_module import ElectricWaterHeatingModule
from modules.district_water_heating_module import DistrictWaterHeatingModule

from modules.sampling_module import SamplingModule


def main():

	start_time = time.time()
	i = 0

	connection = get_connection()

	# Also deletes existing `results' table
	print("Creating table 'results'...")
	create_results_table()

	print("Getting a BAG sample...")
	#sample = get_bag_sample(connection, 1000)
	sample = get_neighbourhoods_sample(connection, 'BU0344%', 1000000)

	print("Initiating modules...")
	# Create neccesary dwelling attributes
	energy_label_module = EnergyLabelModule(connection)
	gas_consumption_comparison_module = GasConsumptionComparisonModule(connection)
	elec_consumption_comparison_module = ElectricityConsumptionComparisonModule(connection)
	# Space heating
	district_space_heating_module = DistrictSpaceHeatingModule(connection)
	gas_space_heating_module = GasSpaceHeatingModule(connection)
	electric_space_heating_module = ElectricSpaceHeatingModule(connection)
	# Water heating
	district_water_heating_module = DistrictWaterHeatingModule(connection)
	gas_water_heating_module = GasWaterHeatingModule(connection)
	electric_water_heating_module = ElectricWaterHeatingModule(connection)
	# Sampling
	sampling_module = SamplingModule(connection)

	print("Processing entries...")
	for entry in sample:
		dwelling = Dwelling(dict(entry), connection)
		# Create neccesary dwelling attributes
		energy_label_module.process(dwelling)
		gas_consumption_comparison_module.process(dwelling)
		elec_consumption_comparison_module.process(dwelling)
		# Space heating
		district_space_heating_module.process(dwelling)
		gas_space_heating_module.process(dwelling)
		electric_space_heating_module.process(dwelling)
		# Water heating
		district_water_heating_module.process(dwelling)
		gas_water_heating_module.process(dwelling)
		electric_water_heating_module.process(dwelling)
		# Sampling
		sampling_module.process(dwelling)
		dwelling.save()
		i += 1
		if i % 100 == 0:
			print(f'   processed dwelling: {i}', end='\r')

	print("\nCommiting and closing...")
	connection.commit()
	connection.close()

	print(f'Processed {i:,} records in {(time.time() - start_time):.2f} seconds.')


if __name__ == "__main__":
	main()
