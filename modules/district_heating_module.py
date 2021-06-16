import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.load_rvo_data()

	def load_rvo_data(self):
		cursor = self.connection.cursor()
		query = "SELECT buurt_code, percentage_stadsverwarming FROM rvo_warmtenetten;"
		cursor.execute(query)
		results = cursor.fetchall()
		# We unpack the rows with tuples into a dict to make it
		# easier to query for the buurt_code later on.
		self.RVO_data = {
			buurt_code: percentage_stadsverwarming
			for (buurt_code, percentage_stadsverwarming)
			in results
		}
		cursor.close()

	def process(self, dwelling):
		super().process(dwelling)
		buurt_id = dwelling.attributes['buurt_id']
		# If the buurt_id is not present in the RVO dataset,
		# we assume there is no district heating,
		# so probability of district heating is 0.
		# We divide by 100 to normalize the probability (given in percentages
		# in the RVO dataset) to between 0 and 1.
		district_heating_p = self.RVO_data.get(buurt_id, 0) / 100
		dwelling.attributes['district_heating_p'] = district_heating_p

	outputs = {
		'district_heating': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'district_heating_p'
		}
	}
