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


class ElectricHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.create_dicts()
		self.heat_pump_probability_modification()

	def create_dicts(self):
		self.buurten_hybrid_heat_pump_data = {}
		self.buurten_elec_low_gas_data = {}
		self.buurten_elec_no_gas_data = {}
		self.postcode_elec_use_data = {}
		self.neighbourhood_elec_check_dict = {}
		self.postcode_household_size_data  ={}

	def load_installation_type_data(self, buurt_id):
		# Add percentage of dwellings with hybrid heat pump in neighbourhood to dict
		cursor = self.connection.cursor()
		query_hybrid_heat_pumps = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050117'AND woningen IS NOT null"
		# A050117 is the code for a gas boiler
		cursor.execute(query_hybrid_heat_pumps, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_hybrid_heat_pump_data[buurt_id] = results[0]

		# Add percentage of dwellings with eelctric heating and low gas use in neighbourhood to dict
		query_low_gas ="SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050118'AND woningen IS NOT null"
		# A050118 is the code for electric heating with low gas use
		cursor.execute(query_low_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_elec_low_gas_data[buurt_id] = results[0]

		# Add percentage of dwellings with eelctric heating and no gas use in neighbourhood to dict
		query_no_gas = "SELECT woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed WHERE area_code = %s AND type_verwarmingsinstallatie LIKE 'A050119'AND woningen IS NOT null"
		# A050119 is the code for electric heating with no gas use
		cursor.execute(query_no_gas, (buurt_id,))
		results = cursor.fetchall()
		self.buurten_elec_no_gas_data[buurt_id] = results[0]
		cursor.close()

	def load_elec_use_data(self, postal_code):
		# Add e;ec use of postal code to dict
		cursor = self.connection.cursor()
		query = "SELECT gemiddelde_elektriciteitslevering_woningen FROM cbs_pc6_2019_energy_use WHERE gemiddelde_elektriciteitslevering_woningen IS NOT NULL AND pc6 = %s"
		cursor.execute(query, (postal_code,))
		results = cursor.fetchall()
		self.postcode_elec_use_data[postal_code] = results[0]
		cursor.close()

	def load_cbs_kerncijfers_data(self, postal_code):
		# Add average pc6 household size to dict
		cursor = self.connection.cursor()
		query = " SELECT gem_hh_gr FROM cbs_pc6_2017_kerncijfers WHERE gem_hh_gr IS NOT null AND pc6 = %s"
		cursor.execute(query, (postal_code,))
		results = cursor.fetchall()
		self.postcode_household_size_data[pc6] = results[0]
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


	def create_benchmark(self, dwelling_characteristics_tuple):

		# Look up electricity use data for dwellings characteristics
		for item in dwelling_characteristics_tuple:
			cursor = self.connection.cursor()
			query_statement = """
			SELECT elektriciteitsleveringen_openbare_net
			FROM cbs_83882ned_elektriciteitslevering_woningkenmerken
			WHERE perioden = '2019'
			AND woningkenmerken LIKE %s
			AND gebruiks_oppervlakteklasse LIKE %s
			AND bewonersklasse_woningen LIKE %s
			AND percentielen NOT LIKE 'Gemiddelde'
			ORDER BY elektriciteitsleveringen_openbare_net
			;"""
			cursor.execute(query_statement, item)
			# Interpolate the data, with extrapolation for <5 and >95 percentile
			results = cursor.fetchall()
			benchmark_y_data = [5, 25, 50, 75, 95]
			benchmark_x_data = [x for x in results]
			benchmark_x_data = list(sum(benchmark_x_data, ()))
			if None in benchmark_x_data or benchmark_x_data == []:
				# Need to find a way to make this have results. Query for totaal? How to find the characteristic that is the culprit?
				pass
			else:
				interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
		return interpolated_function

	def neighbourhood_elec_use_comparison(self,buurt_id):
		# Output: Dictionary with vbo_id:percentile electricity use
		percentile_elec_use_dict = {}
		connection = get_connection()
		# Get all dwellings in the neighbourhood
		sample = get_neighbourhood_dwellings(connection, buurt_id)

		for entry in sample:
			dwelling = Dwelling(dict(entry), connection)
			vbo_id = dwelling.attributes['vbo_id']
			postal_code = dwelling.attributes['pc6']

			# Electricity use in postal code
			if postal_code not in self.postcode_elec_use_data:
				energy_label_module.process(connection)
			postal_code_elec_use = self.postcode_elec_use_data[postal_code]

			# Get dwellings attributes
			floor_space = dwelling.attributes['oppervlakte']
			building_type = dwelling.attributes['woningtype']
			if postal_code not in self.postcode_household_size_data:
				self.load_cbs_kerncijfers_data(postal_code)
			household_size = round(self.postcode_household_size_data[postal_code])
			if household_size <= 0:
				household_size = 1
			try:
				 energy_label = dwelling.attributes['energy_label']
			except KeyError:
				self.get_energy_label[vbo_id]
				self.assign_energy_label[dwelling]
				energy_label = dwelling.attributes['energy_label']

			# Get electricity use per person for comparison with benchmark
			dwelling_elec_use_per_person = postal_code_elec_use / household_size

			# Harmonize building type terminology between bag and CBS
			if building_type == 'twee_onder_1_kap':
				building_type = '2-onder-1-kapwoning'
			elif building_type =='tussenwoning':
				building_type = 'Tussenwoning'
			elif building_type == 'vrijstaand':
				building_type = 'Vrijstaande woning'
			elif building_type == 'hoekwoning':
				building_type = 'Hoekwoning'
			elif building_type == 'meergezinspand_hoog':
				building_type = 'Appartement'
			elif building_type == 'meergezinspand_laag_midden':
				building_type = 'Appartement'

			# Make floor areas searchable
			if floor_space < 50:
				floor_space_string = '15 tot 50 m²'
			elif floor_space >= 50 and floor_space < 75:
				floor_space_string = '50 tot 75 m²'
			elif floor_space >= 75 and floor_space < 100:
				floor_space_string = '75 tot 100 m²'
			elif floor_space >= 100 and floor_space < 150:
				floor_space_string = '100 tot 150 m²'
			elif floor_space >= 150 and floor_space < 250:
				floor_space_string = '150 tot 250 m²'
			elif floor_space >= 250:
				floor_space_string = '250 tot 500 m²'

			# Make household sizes searchable
			if household_size == 1:
				household_size_string = '1 persoon'
			elif household_size == 2:
				household_size_string = '2 personen'
			elif household_size == 3:
				household_size_string = '3 personen'
			elif household_size == 4:
				household_size_string = '4 personen'
			elif household_size >= 5:
				household_size_string = '5 personen of meer'

			# Default value for percentile
			dwelling_elec_use_percentile = 0
			dwelling_characteristics_tuple = (building_type, floor_space_string, household_size_string)

			# Get benchmark for specific dwelling type, floor space and number of inhabitants
			if dwelling_characteristics_tuple not in self.gas_benchmark_dict:
				self.gas_benchmark_dict[dwelling_characteristics_tuple] = self.create_benchmark(dwelling_characteristics_tuple)

			benchmark = self.elec_benchmark_dict[dwelling_characteristics_tuple]

			# If there is not electricity use, we cannot compare
			if postal_code_elec_use == 0:
				pass
			# If there is not benchmark data, we cannot compare
			# TODO: set benchmark to more general data in def create_benchmark(self) if no data is available
			elif benchmark == None:
				pass
			else:
				# See where electricity use compares against the interpolated benchmark
				dwelling_elec_use_percentile = float(benchmark(dwelling_elec_use_per_person))/100
				# Extrapolation can give values outside of the domain
				if dwelling_elec_use_percentile < 0:
					dwelling_elec_use_percentile = 0
				elif dwelling_elec_use_percentile > 1:
					dwelling_elec_use_percentile = 1
				else:
					pass
			percentile_elec_use_dict[vbo_id] = dwelling_elec_use_percentile
		return(percentile_elec_use_dict)

	def process(self, dwelling):
		super().process(dwelling)

		# Get basic dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		energy_label = dwelling.attributes['energy_label']

		# Base probability of having different types of electric heating
		if buurt_id not in self.buurten_hybrid_heat_pump_data:
			self.load_installation_type_data(buurt_id)
		hybrid_heat_pump_p = self.buurten_hybrid_heat_pump_data[buurt_id] / 100
		elec_low_gas_p = self.buurten_elec_low_gas_data[buurt_id] / 100
		elec_no_gas_p = self.buurten_elec_no_gas__data[buurt_id] / 100

		# Placeholder electric boiler probability
		elec_boiler_p = elec_low_gas_p + elec_no_gas_p

		# Check if neighbourhood has already been through the electricity usage ranking process
		if buurt_id not in self.neighbourhood_elec_check_dict:
			# If not, add to the dictionary
			self.neighbourhood_elec_check_dict[buurt_id] = self.neighbourhood_elec_use_comparison(buurt_id)
		elec_use_percentile_national = self.neighbourhood_elec_check_dict[buurt_id][vbo_id]

		# Check electricty consumption percentile ranking within neighbourhood
		sorted_usage = list({k: v for k, v in sorted(self.neighbourhood_elec_check_dict[buurt_id].items(), key=lambda item: item[1])}.items())
		# Find the index of the dwelling in question
		index = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id].pop()
		# Calculate the ranking of the dwelling [0,1]
		elec_use_percentile_neighbourhood = (index+1)/len(sorted_usage)

		# Modify probabilities for heat pumps
		# We assume there are only electric heat pumps in dwellings with energylabel C or higher
		if energy_label == 'A+++' or energy_label == 'A++' or energy_label == 'A+' or energy_label == 'A' or energy_label == 'B' or energy_label == 'C':
			electric_heat_pump_p = self.electric_heat_pump_p
		else:
			electric_heat_pump_p = 0.

		# If there is a high electricity use we modify the probability of the hybrid heat pump according to the gas use
		gas_use_percentile_national = dwelling.attributes['gas_use_percentile_national']
		if elec_use_percentile_national > 0.7:
			hybrid_heat_pump_p = self.modify_probability(hybrid_heat_pump_p, gas_use_percentile_national)

		# Modify probabilities for electric boiler
		elec_boiler_p = self.modify_probability(elec_boiler_p, elec_use_percentile_neighbourhood)

		dwelling.attributes['elec_use_percentile_national'] = elec_use_percentile_national
		dwelling.attributes['elec_use_percentile_neighbourhood'] = elec_use_percentile_neighbourhood
		dwelling.attributes['electric_heat_pump_p'] = electric_heat_pump_p
		dwelling.attributes['hybrid_heat_pump_p'] = hybrid_heat_pump_p
		dwelling.attributes['elec_boiler_p'] = elec_boiler_p

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
			'distribution': 'elec_boiler_p'
		},
		'elec_boiler_p': {
			'type': 'float',
			'sampling': False,
		}
	}