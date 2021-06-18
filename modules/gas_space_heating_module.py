import os
import sys

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasSpaceHeatingModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection)
		self.buurten_boiler_heating_data = {}
		self.buurten_block_heating_data = {}
		self.buurten_district_high_gas_data = {}

	def load_installation_type_data(self, buurt_id):
		# Add percentage of dwellings with gas boiler in neighbourhood to dict
		cursor = self.connection.cursor()
		query = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050112'AND woningen IS NOT null"
		# A050112 is the code for a gas boiler
		cursor.execute(query, (buurt_id,))
		results = cursor.fetchall()
		if results is not None:
			results = results[0][0]
		self.buurten_boiler_heating_data[buurt_id] = results

		# Add percentage of dwellings with block heating in neighbourhood to dict
		query = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050113'AND woningen IS NOT null"
		# A050113 is the code for a block heating
		cursor.execute(query, (buurt_id,))
		results = cursor.fetchall()
		if results is not None:
			results = results[0][0]
		self.buurten_block_heating_data[buurt_id] = results

		# Add percentage of dwellings with district heating and high gas use
		cursor = self.connection.cursor()
		query_district_high_gas = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050114'AND woningen IS NOT null"
		# A050114 is the code for district heating with high gas use
		cursor.execute(query_district_high_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_district_high_gas_data[buurt_id] = results[0][0]
		cursor.close()

	def process(self, dwelling):
		super().process(dwelling)

		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		# Get base probability of having different heating types
		if buurt_id not in self.buurten_boiler_heating_data:
 			self.load_installation_type_data(buurt_id)
		boiler_heating_space_p = self.buurten_boiler_heating_data.get(buurt_id, 0) / 100
		block_heating_space_p = self.buurten_block_heating_data.get(buurt_id, 0) / 100
		district_high_space_p = self.buurten_district_high_gas_data.get(buurt_id, 0) / 100

		gas_boiler_space_p = boiler_heating_space_p + district_high_space_p
		gas_boiler_space_p = self.modify_probability_up(gas_boiler_space_p, gas_use_percentile_neighbourhood)
		block_heating_space_p = self.modify_probability_up(block_heating_space_p, gas_use_percentile_neighbourhood)

		dwelling.attributes['boiler_heating_space_p'] = boiler_heating_space_p
		dwelling.attributes['district_high_space_p'] = district_high_space_p
		dwelling.attributes['gas_boiler_space_p'] = gas_boiler_space_p
		dwelling.attributes['block_heating_space_p'] = block_heating_space_p

	outputs = {
		'gas_boiler_space': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'gas_boiler_space_p'
		},
		'gas_boiler_space_p': {
			'type': 'float',
			'sampling': False,
		},
		'block_heating_space': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'block_heating_space_p'
		},
		'block_heating_space_p': {
			'type': 'float',
			'sampling': False,
		}
	}
