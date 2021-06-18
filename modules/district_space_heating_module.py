import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictSpaceHeatingModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection)

	def process(self, dwelling):
		super().process(dwelling)
		# Get dwelling attributes
		buurt_id = dwelling.attributes['buurt_id']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		# Base probability of having different types of electric heating
		district_high_gas_p = buurt.attributes['district_high_gas_share']
		district_low_gas_p = buurt.attributes['district_low_gas_share']
		district_no_gas_p = buurt.attributes['district_no_gas_share']

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

class DistrictSpaceHeatingRegionalModule(BaseModule):

	def process_buurt(self, buurt):
		self.add_installation_type_shares(buurt)

	def add_installation_type_shares(self, buurt):

		buurt_id = buurt.attributes['buurt_id']
		cursor = self.connection.cursor()

		# Add percentage of dwellings with gas boiler in neighbourhood to dict
		# A050114 is the code for district heating with high gas use
		query_district_high_gas='''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050114'
			AND woningen IS NOT null'''
		cursor.execute(query_district_high_gas, (buurt_id,))
		buurt.attributes['district_high_gas_share'] = cursor.fetchone()[0]

		# Add percentage of dwellings with block heating in neighbourhood to dict
		# A050115 is the code for district heating with low gas use
		query_district_low_gas ='''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050115'
			AND woningen IS NOT null'''
		cursor.execute(query_district_low_gas, (buurt_id,))
		buurt.attributes['district_low_gas_share'] = cursor.fetchone()[0]

		# Add percentage of dwellings with block heating in neighbourhood to dict
		# A050116 is the code for district heating with no gas use
		query_district_no_gas ='''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050116'
			AND woningen IS NOT null'''
		cursor.execute(query_district_no_gas, (buurt_id,))
		buurt.attributes['district_no_gas_share'] = cursor.fetchone()[0]

		cursor.close()

	supports = ['buurt']
