import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictSpaceHeatingModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection)
		self.buurten_district_high_gas_data = {}
		self.buurten_district_low_gas_data = {}
		self.buurten_district_no_gas_data = {}

	def load_installation_type_data(self, buurt_id):
		# Add percentage of dwellings with district heating and high gas use
		cursor = self.connection.cursor()
		query_district_high_gas = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050114'AND woningen IS NOT null"
		# A050114 is the code for district heating with high gas use
		cursor.execute(query_district_high_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_district_high_gas_data[buurt_id] = results[0][0]

		# Add percentage of dwellings with district heating and low gas use in neighbourhood to dict
		query_district_low_gas ="SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050115'AND woningen IS NOT null"
		# A050115 is the code for district heating with low gas use
		cursor.execute(query_district_low_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_district_low_gas_data[buurt_id] = results[0][0]

		# Add percentage of dwellings with district heating and no gas use in neighbourhood to dict
		query_district_no_gas = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050116'AND woningen IS NOT null"
		# A050116 is the code for district heating with no gas use
		cursor.execute(query_district_no_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_district_no_gas_data[buurt_id] = results[0][0]
		cursor.close()

	def process(self, dwelling):
		super().process(dwelling)
		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		postal_code = dwelling.attributes['pc6']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		# Base probability of having different types of electric heating
		if buurt_id not in self.buurten_district_high_gas_data:
			self.load_installation_type_data(buurt_id)
		district_high_gas_p = self.buurten_district_high_gas_data[buurt_id] / 100
		district_low_gas_p = self.buurten_district_low_gas_data[buurt_id] / 100
		district_no_gas_p = self.buurten_district_no_gas_data[buurt_id] / 100

		# Modify probabilities according to gas use
		district_high_gas_p = self.modify_probability_up(district_high_gas_p, gas_use_percentile_neighbourhood)
		district_low_gas_p = self.modify_probability_down(district_low_gas_p, gas_use_percentile_neighbourhood)

		dwelling.attributes['district_high_gas_p'] = district_high_gas_p
		dwelling.attributes['district_low_gas_p'] = district_low_gas_p
		dwelling.attributes['district_no_gas_p'] = district_no_gas_p
		dwelling.attributes['district_heating_space_p'] = district_high_gas_p + district_low_gas_p + district_no_gas_p

	outputs = {
		'district_heating_space': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'district_heating_space_p'
		},
		'district_heating_space_p': {
			'type': 'float',
			'sampling': False,
		}
	}
