import time

from psycopg2 import sql

from utils.database_utils import get_connection, get_bag_sample
from utils.create_results_table import main as create_results_table

from modules.dwelling import Dwelling

from modules.district_heating_module import DistrictHeatingModule
from modules.gas_boiler_module import GasBoilerModule
from modules.electric_heating_module import ElectricHeatingModule
from modules.sampling_module import SamplingModule


def main():

	start_time = time.time()
	i = 0

	connection = get_connection()

	# Also deletes existing `results' table
	print("Creating table 'results'...")
	create_results_table()

	print("Getting a BAG sample...")
	sample = get_bag_sample(connection, n=1000)

	print("Initiating modules...")
	district_heating_module = DistrictHeatingModule(connection)
	gas_boiler_module = GasBoilerModule(connection)
	electric_heating_module = ElectricHeatingModule(connection)
	sampling_module = SamplingModule(connection)

	print("Processing entries...")
	for entry in sample:
		dwelling = Dwelling(dict(entry), connection)
		district_heating_module.process(dwelling)
		gas_boiler_module.process(dwelling)
		electric_heating_module.process(dwelling)
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
