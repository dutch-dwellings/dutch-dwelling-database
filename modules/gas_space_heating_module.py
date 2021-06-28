import os
import sys

sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasSpaceHeatingModule(BaseModule):

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		buurt = dwelling.regions['buurt']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']

		# Get base probability of having different heating types
		boiler_heating_space_p = buurt.attributes['gas_boiler_heating_share']
		block_heating_space_p_base = buurt.attributes['gas_block_heating_share']
		district_high_space_p = buurt.attributes['district_high_gas_share']

		gas_boiler_space_p = boiler_heating_space_p + 0.5 * district_high_space_p
		block_heating_space_p = block_heating_space_p_base + 0.5 * district_high_space_p # 0.5 could be improved by looking for literature
		gas_boiler_space_p = self.modify_probability_up(gas_boiler_space_p, gas_use_percentile_neighbourhood)
		block_heating_space_p = self.modify_probability_up(block_heating_space_p, gas_use_percentile_neighbourhood)

		dwelling.attributes['boiler_heating_space_p'] = boiler_heating_space_p
		dwelling.attributes['district_high_space_p'] = district_high_space_p
		dwelling.attributes['gas_boiler_space_p'] = gas_boiler_space_p
		dwelling.attributes['block_heating_space_p'] = block_heating_space_p
		dwelling.attributes['block_heating_space_p_base'] = block_heating_space_p_base

	outputs = {
		'gas_boiler_space': {
			'type': 'boolean',
			'function' : 'space',
			'sampling': True,
			'report' : False,
			'distribution': 'gas_boiler_space_p'
		},
		'gas_boiler_space_p': {
			'type': 'float',
			'sampling': False,
		},
		'block_heating_space': {
			'type': 'boolean',
			'function' : 'space',
			'sampling': True,
			'report' : False,
			'distribution': 'block_heating_space_p'
		},
		'block_heating_space_p': {
			'type': 'float',
			'sampling': False,
		}
	}

class GasSpaceHeatingRegionalModule(BaseModule):

	def process_buurt(self, buurt):
		self.add_installation_type_shares(buurt)

	def add_installation_type_shares(self, buurt):

		buurt_id = buurt.attributes['buurt_id']
		cursor = self.connection.cursor()

		# Add percentage of dwellings with gas boiler in neighbourhood to dict
		# A050112 is the code for a gas boiler
		query_boiler_heating ='''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050112'
			AND woningen IS NOT null'''
		cursor.execute(query_boiler_heating, (buurt_id,))


		gas_boiler_heating_share = cursor.fetchone()
		gas_boiler_heating_share = self.handle_null_data(gas_boiler_heating_share)

		buurt.attributes['gas_boiler_heating_share'] = gas_boiler_heating_share

		# Add percentage of dwellings with block heating in neighbourhood to dict
		# A050113 is the code for a block heating
		query_block_heating ='''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050113'
			AND woningen IS NOT null'''
		cursor.execute(query_block_heating, (buurt_id,))

		gas_block_heating_share = cursor.fetchone()
		gas_block_heating_share = self.handle_null_data(gas_block_heating_share)

		buurt.attributes['gas_block_heating_share'] = gas_block_heating_share

		cursor.close()

	supports = ['buurt']
