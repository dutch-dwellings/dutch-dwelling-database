import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictWaterHeatingModule(BaseModule):

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']
		elec_use_percentile_neighbourhood = dwelling.attributes['elec_use_percentile_neighbourhood']
		district_high_gas_p = dwelling.attributes['district_high_gas_p']
		district_low_gas_p = dwelling.attributes['district_low_gas_p']
		district_no_gas_p = dwelling.attributes['district_no_gas_p']

		# Water district heating
		district_heating_water_p = 0.5 * district_high_gas_p + 0.5 * 0.5 * district_low_gas_p + 0.5 * district_no_gas_p  # 0.5 could be improved by looking for literature
		district_heating_water_p = self.modify_probability_down(district_heating_water_p, gas_use_percentile_neighbourhood)
		district_heating_water_p = self.modify_probability_down(district_heating_water_p, elec_use_percentile_neighbourhood)

		dwelling.attributes['district_heating_water_p'] = district_heating_water_p

	outputs = {
		'district_heating_water': {
			'type': 'boolean',
			'sampling': True,
			'function' : 'water',
			'report' : False,
			'distribution': 'district_heating_water_p'
			},
		'district_heating_water_p': {
			'type': 'float',
			'sampling': False,
			}
	}
