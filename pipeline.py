import pprint
import time

from psycopg2 import sql

from utils.database_utils import get_connection, get_bag_sample, insert_dict
from utils.create_results_table import main as create_results_table
from modules.district_heating_module import DistrictHeatingModule
from modules.gas_boiler_module import GasBoilerModule
from modules.electric_heating_module import ElectricHeatingModule
from modules.sampling_module import SamplingModule

class Dwelling:

	def __init__(self, attributes, connection):
		self.attributes = attributes
		self.connection = connection
		# We copy the list so we get an instance variable
		# instead of a class variable.
		self.outputs = self.default_outputs.copy()
		self.sampling_outputs = {}

	def __str__(self):
		pp = pprint.PrettyPrinter(indent=4)
		return f'Dwelling {self.attributes["identificatie"]}:\nattributes:\n{pp.pformat(self.attributes)}\noutputs:\n{pp.pformat(self.outputs)}'

	def __repr__(self):
		return f'Dwelling(attributes={repr(self.attributes)}, connection={repr(self.connection)})'

	def get_filtered_attributes(self):
		'''
		Get the attributes and their values
		that need to be output to the database.
		'''
		return {key: val for (key, val) in self.attributes.items() if key in self.outputs or key in self.sampling_outputs.keys()}

	def save(self):
		'''
		INSERT the generated Dwelling object
		into the 'results' database.
		'''
		cursor = self.connection.cursor()

		row_dict = self.get_filtered_attributes()
		insert_dict(
			table_name='results',
			row_dict = row_dict,
			cursor = cursor
		)

		cursor.close()

	# This defines the default outputs irrespective of which
	# modules are active. Specify the outputs for specific modules
	# within the class definition of that module.
	#
	# This has to match the default 'results'
	# table layout as defined in utils/create_results_table.sql.
	# In other words: columns have to exist for all the
	# default_outputs.
	#
	# As of now, we can only assume that BAG-data is always present,
	# so only use BAG column_names here.
	default_outputs = ['identificatie']


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
