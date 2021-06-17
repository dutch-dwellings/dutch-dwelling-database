import os
import sys
from scipy.interpolate import interp1d
import itertools
import math
import collections
from utils.database_utils import get_connection, get_neighbourhood_dwellings
from modules.dwelling import Dwelling
from modules.energy_label_module import EnergyLabelModule

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class ElectricSpaceHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.create_dicts()
		self.heat_pump_probability_modification()

	def create_dicts(self):
		self.buurten_hybrid_heat_pump_data = {}
		self.buurten_elec_low_gas_data = {}
		self.buurten_elec_no_gas_data = {}

	def load_installation_type_data(self, buurt_id):
		# Add percentage of dwellings with hybrid heat pump in neighbourhood to dict
		cursor = self.connection.cursor()
		query_hybrid_heat_pumps = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050117'AND woningen IS NOT null"
		# A050117 is the code for a gas boiler
		cursor.execute(query_hybrid_heat_pumps, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_hybrid_heat_pump_data[buurt_id] = results[0][0]

		# Add percentage of dwellings with eelctric heating and low gas use in neighbourhood to dict
		query_low_gas ="SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050118'AND woningen IS NOT null"
		# A050118 is the code for electric heating with low gas use
		cursor.execute(query_low_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_elec_low_gas_data[buurt_id] = results[0][0]

		# Add percentage of dwellings with eelctric heating and no gas use in neighbourhood to dict
		query_no_gas = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050119'AND woningen IS NOT null"
		# A050119 is the code for electric heating with no gas use
		cursor.execute(query_no_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_elec_no_gas_data[buurt_id] = results[0][0]
		cursor.close()

	def heat_pump_probability_modification(self):
		cursor = self.connection.cursor()
		# create dictionary with buurt_id and number of dwellings
		query = "SELECT COUNT(energieklasse) FROM energy_labels"
		cursor.execute(query)
		results = cursor.fetchall()
		total_dwellings_with_energy_label = float(results[0][0])

		query = "SELECT COUNT(energieklasse) FROM energy_labels WHERE energieklasse = 'A+++' OR energieklasse = 'A++' OR energieklasse = 'A+' OR energieklasse = 'A' OR energieklasse = 'B' OR energieklasse = 'C'"
		cursor.execute(query)
		heat_pump_eligible_dwellings = float(results[0][0])
		cursor.close()
		# Probability is increased using new% = (old% * N_nbh)/(N_eligible)
		self.electric_heat_pump_p = 0.0155 * total_dwellings_with_energy_label/heat_pump_eligible_dwellings # 0.0155 base percentage taken from WoON

	def process(self, dwelling):
		super().process(dwelling)

		# Get basic dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		energy_label = dwelling.attributes['energy_label']
		gas_use_percentile_national = dwelling.attributes['gas_use_percentile_national']
		elec_use_percentile_national = dwelling.attributes['elec_use_percentile_national']
		elec_use_percentile_neighbourhood = dwelling.attributes['elec_use_percentile_neighbourhood']

		# Base probability of having different types of electric heating
		if buurt_id not in self.buurten_hybrid_heat_pump_data:
			self.load_installation_type_data(buurt_id)
		hybrid_heat_pump_p = self.buurten_hybrid_heat_pump_data[buurt_id] / 100
		elec_low_gas_p = self.buurten_elec_low_gas_data[buurt_id] / 100
		elec_no_gas_p = self.buurten_elec_no_gas_data[buurt_id] / 100

		# Modify probabilities for heat pumps
		# We assume there are only electric heat pumps in dwellings with energylabel C or higher
		if energy_label == 'A+++' or energy_label == 'A++' or energy_label == 'A+' or energy_label == 'A' or energy_label == 'B' or energy_label == 'C':
			electric_heat_pump_p = self.electric_heat_pump_p
		else:
			electric_heat_pump_p = 0.

		# If there is a high electricity use we modify the probability of the hybrid heat pump according to the gas use

		if elec_use_percentile_national > 0.7:
			hybrid_heat_pump_p = self.modify_probability(hybrid_heat_pump_p, gas_use_percentile_national)

		# Modify probabilities for electric boiler
		elec_low_gas_p = self.modify_probability(elec_low_gas_p, elec_use_percentile_neighbourhood)
		elec_no_gas_p = self.modify_probability(elec_no_gas_p, elec_use_percentile_neighbourhood)

		dwelling.attributes['hybrid_heat_pump_p'] = hybrid_heat_pump_p
		dwelling.attributes['electric_heat_pump_p'] = electric_heat_pump_p
		dwelling.attributes['elec_boiler_space_p'] = elec_low_gas_p + elec_no_gas_p
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
		},
		'elec_low_gas_p': {
			'type': 'float',
			'sampling': False,
		},
		'elec_no_gas_p': {
			'type': 'float',
			'sampling': False,
		}
	}
