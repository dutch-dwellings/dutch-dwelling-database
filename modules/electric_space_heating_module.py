import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class ElectricSpaceHeatingModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection)
		self.electric_heat_pump_base_p = self.get_electric_heat_pump_base_p()

	def get_electric_heat_pump_base_p(self):
		'''
		Get the base probability of a dwelling having a heat pump,
		assuming only building with an energy label C or higher
		have a heat pump.
		Uses data from the WoON survey to establish national percentage
		of dwellings with heat pump.
		Uses data from the BAG to get the total number of dwellings.
		'''
		# National percentage of dwellings with heat pump,
		# estimated from the WoON survey.
		WOON_HEAT_PUMP_P = 0.0155

		cursor = self.connection.cursor()

		dwellings_count_query = "SELECT COUNT(vbo_id) FROM bag"
		cursor.execute(dwellings_count_query)
		dwellings_count = cursor.fetchone()[0]

		c_plus_labels_count_query = "SELECT COUNT(energieklasse) FROM energy_labels WHERE energieklasse >= 'C'"
		cursor.execute(c_plus_labels_count_query)
		heat_pump_eligible_dwellings = cursor.fetchone()[0]

		cursor.close()
		print(dwellings_count)
		print(heat_pump_eligible_dwellings)
		print(WOON_HEAT_PUMP_P * dwellings_count / heat_pump_eligible_dwellings)
		return WOON_HEAT_PUMP_P * dwellings_count / heat_pump_eligible_dwellings

	def process(self, dwelling):
		super().process(dwelling)

		# Get dwelling attributes
		energy_label = dwelling.attributes['energy_label']
		gas_use_percentile_national = dwelling.attributes['gas_use_percentile_national']
		gas_use_percentile_neighbourhood = dwelling.attributes['gas_use_percentile_neighbourhood']
		elec_use_percentile_national = dwelling.attributes['elec_use_percentile_national']
		elec_use_percentile_neighbourhood = dwelling.attributes['elec_use_percentile_neighbourhood']

		buurt = dwelling.regions['buurt']
		# Base probability of having different types of electric heating
		elec_high_gas_p = buurt.attributes['elec_high_gas_share']
		elec_low_gas_p  = buurt.attributes['elec_low_gas_share']
		elec_no_gas_p   = buurt.attributes['elec_no_gas_share']

		# Modify probabilities for heat pumps
		# We assume there are only electric heat pumps in dwellings with energylabel C or higher
		if energy_label in ['A+++++', 'A++++', 'A+++', 'A++', 'A+', 'A', 'B', 'C']:
			electric_heat_pump_p = self.electric_heat_pump_base_p
		else:
			electric_heat_pump_p = 0.

		# If there is a high electricity use we modify the probability of the hybrid heat pump according to the gas use
		hybrid_heat_pump_p = elec_high_gas_p
		if elec_use_percentile_national > 0.7:
			hybrid_heat_pump_p = self.modify_probability_up(elec_high_gas_p, gas_use_percentile_national)

		# Modify probabilities for electric boiler
		elec_boiler_space_p = elec_low_gas_p + elec_no_gas_p
		elec_boiler_space_p = self.modify_probability_up(elec_boiler_space_p, elec_use_percentile_neighbourhood)
		elec_boiler_space_p = self.modify_probability_down(elec_boiler_space_p, gas_use_percentile_neighbourhood)

		dwelling.attributes['hybrid_heat_pump_p'] = hybrid_heat_pump_p
		dwelling.attributes['electric_heat_pump_p'] = electric_heat_pump_p
		dwelling.attributes['elec_boiler_space_p'] = elec_boiler_space_p
		dwelling.attributes['elec_high_gas_p'] = elec_high_gas_p
		dwelling.attributes['elec_low_gas_p'] = elec_low_gas_p
		dwelling.attributes['elec_no_gas_p'] = elec_no_gas_p

	outputs = {
		'hybrid_heat_pump': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'hybrid_heat_pump_p'
		},
		'hybrid_heat_pump_p': {
			'type': 'float',
			'sampling': False,
		},
		'electric_heat_pump': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'electric_heat_pump_p'
		},
		'electric_heat_pump_p': {
			'type': 'float',
			'sampling': False,
		},
		'electric_boiler': {
			'type': 'boolean',
			'sampling': True,
			'distribution': 'elec_boiler_space_p'
		},
		'elec_boiler_space_p': {
			'type': 'float',
			'sampling': False,
		}
	}

class ElectricSpaceHeatingRegionalModule(BaseModule):

	def process_buurt(self, buurt):
		self.add_installation_type_shares(buurt)

	def add_installation_type_shares(self, buurt):

		buurt_id = buurt.attributes['buurt_id']
		cursor = self.connection.cursor()

		# Add share of dwellings with hybrid heat pump
		# A050117 is the code for a gas boiler
		query_hybrid_heat_pumps = '''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050117'
			AND woningen IS NOT null'''
		cursor.execute(query_hybrid_heat_pumps, (buurt_id,))
		buurt.attributes['elec_high_gas_share'] = cursor.fetchone()[0]

		# Add share of dwellings with electric heating and low gas use
		# A050118 is the code for electric heating with low gas use
		query_low_gas = '''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050118'
			AND woningen IS NOT null'''
		cursor.execute(query_low_gas, (buurt_id,))
		buurt.attributes['elec_low_gas_share'] = cursor.fetchone()[0]

		# Add share of dwellings with electric heating and no gas use
		# A050119 is the code for electric heating with no gas use
		query_no_gas = '''
		SELECT woningen::float / 100
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE
			area_code = %s
			AND type_verwarmingsinstallatie = 'A050119'
			AND woningen IS NOT null'''
		cursor.execute(query_no_gas, (buurt_id,))
		buurt.attributes['elec_no_gas_share'] = cursor.fetchone()[0]

		cursor.close()

	supports = ['buurt']
