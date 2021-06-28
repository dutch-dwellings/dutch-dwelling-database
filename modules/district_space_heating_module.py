import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule, BaseRegionalModule

class DistrictSpaceHeatingModule(BaseModule):

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		buurt = dwelling.regions['buurt']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		# Base probability of having different types of electric heating
		district_high_gas_p = buurt.attributes['district_high_gas_share']
		district_low_gas_p = buurt.attributes['district_low_gas_share']
		district_no_gas_p = buurt.attributes['district_no_gas_share']

		# Modify probabilities according to gas use
		district_high_gas_p_mod = self.modify_probability_up(district_high_gas_p, gas_use_percentile_neighbourhood)
		district_low_gas_p_mod = self.modify_probability_down(district_low_gas_p, gas_use_percentile_neighbourhood)

		dwelling.attributes['district_high_gas_p'] = district_high_gas_p
		dwelling.attributes['district_low_gas_p'] = district_low_gas_p
		dwelling.attributes['district_no_gas_p'] = district_no_gas_p
		dwelling.attributes['district_heating_space_p'] = district_high_gas_p + district_low_gas_p + district_no_gas_p

	outputs = {
		'district_heating_space': {
			'type': 'boolean',
			'sampling': True,
			'function' : 'space',
			'report' : False,
			'distribution': 'district_heating_space_p'
		},
		'district_heating_space_p': {
			'type': 'float',
			'sampling': False,
		}
	}

class DistrictSpaceHeatingRegionalModule(BaseRegionalModule):

	def process_buurt(self, buurt):
		self.calculate_probability_modifier(buurt)
		self.add_installation_type_shares(buurt)

	def calculate_probability_modifier(self, buurt):
		buurt_id = buurt.attributes['buurt_id']

		cursor = self.connection.cursor()
		# Calcultae total percentage of dwelling in neighbourhood with
		total_percentage_query='''
		SELECT SUM(woningen)
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE area_code = %s
		'''
		cursor.execute(total_percentage_query, (buurt_id,))
		total_percentage = cursor.fetchone()[0]
		probability_modifier = 100 / total_percentage
		buurt.attributes['probability_modifier'] = probability_modifier

	def add_installation_type_shares(self, buurt):

		buurt_id = buurt.attributes['buurt_id']
		cursor = self.connection.cursor()
		probability_modifier = buurt.attributes['probability_modifier']
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

		district_high_gas_share = cursor.fetchone()
		district_high_gas_share = self.handle_null_data(district_high_gas_share)

		buurt.attributes['district_high_gas_share'] = district_high_gas_share * probability_modifier
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

		district_low_gas_share = cursor.fetchone()
		district_low_gas_share = self.handle_null_data(district_low_gas_share)

		buurt.attributes['district_low_gas_share'] = district_low_gas_share * probability_modifier

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
		district_no_gas_share = cursor.fetchone()
		district_no_gas_share = self.handle_null_data(district_no_gas_share)

		buurt.attributes['district_no_gas_share'] = district_no_gas_share  * probability_modifier

		cursor.close()

	supports = ['buurt']
