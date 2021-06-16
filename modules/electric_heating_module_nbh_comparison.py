import os
import sys
from scipy.interpolate import interp1d
import itertools
import math
import collections
from utils.database_utils import get_connection, get_neighbourhood_dwellings
from modules.dwelling import Dwelling
# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class ElectricHeatingModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.load_installation_type_data()
		self.load_elec_use_data()
		self.load_cbs_kerncijfers_data()
		self.load_num_dwellings_in_neighbourhood()
		self.load_neighbourhood_dwelling_data()
		self.create_benchmark()

	def load_installation_type_data(self):
		# create dictionary with buurt_id and percentage of gas boilers
		cursor = self.connection.cursor()
		query_hybrid_heat_pumps = '''
		SELECT area_code, woningen
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE (area_code LIKE 'BU%')
		AND type_verwarmingsinstallatie LIKE 'A050117'
		AND woningen IS NOT null
		'''
		cursor.execute(query_hybrid_heat_pumps)
		results = cursor.fetchall()
		self.buurten_hybrid_heat_pump_data = {
		buurt_id: hybrid_heat_pump_percentage
		for (buurt_id, hybrid_heat_pump_percentage)
		in results
		}

		query_low_gas = '''
		SELECT area_code, woningen
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE (area_code LIKE 'BU%')
		AND type_verwarmingsinstallatie LIKE 'A050118'
		AND woningen IS NOT null
		'''
		cursor.execute(query_low_gas)
		results = cursor.fetchall()
		self.buurten_elec_low_gas_data = {
		buurt_id: low_gas_percentage
		for (buurt_id, low_gas_percentage)
		in results
		}

		query_no_gas = '''
		SELECT area_code, woningen
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019_typed
		WHERE (area_code LIKE 'BU%')
		AND type_verwarmingsinstallatie LIKE 'A050119'
		AND woningen IS NOT null
		'''
		cursor.execute(query_no_gas)
		results = cursor.fetchall()
		self.buurten_elec_no_gas__data = {
		buurt_id: no_gas_percentage
		for (buurt_id, no_gas_percentage)
		in results
		}
		cursor.close()

	def load_elec_use_data(self):
		# Create dictionary which relates the postal code of a dwelling and the electricity use of that postal code
		cursor = self.connection.cursor()
		query = "SELECT pc6, gemiddelde_elektriciteitslevering_woningen FROM cbs_pc6_2019_energy_use WHERE gemiddelde_elektriciteitslevering_woningen IS NOT NULL;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.postcode_elec_use_data = {
		postcode: elec_use
		for (postcode, elec_use)
		in results
		}
		cursor.close()

	def load_cbs_kerncijfers_data(self):
		# Create a dictionary that relates the postal code of a dwelling and the average household size
		cursor = self.connection.cursor()
		query = '''
		SELECT pc6, gem_hh_gr FROM cbs_pc6_2017_kerncijfers WHERE gem_hh_gr IS NOT null;
		'''
		cursor.execute(query)
		results = cursor.fetchall()
		self.postcode_household_size_data = {
		postcode: household_size
		for (postcode, household_size)
		in results
		}
		cursor.close()

	def load_num_dwellings_in_neighbourhood(self):
		cursor = self.connection.cursor()
		# create dictionary with buurt_id and number of dwellings
		query = "SELECT buurt_id, COUNT(vbo_id) FROM bag GROUP BY buurt_id"
		cursor.execute(query)
		results = cursor.fetchall()
		self.num_dwellings_in_neighbourhood = {
			buurt_id: num_dwellings
			for (buurt_id, num_dwellings)
			in results
		}
		cursor.close()

	def load_neighbourhood_dwelling_data(self):
		# Create dictionary which relates the neighbourhood code of a dwelling and the dwellings in that neighbourhood
		cursor = self.connection.cursor()
		query = "SELECT buurt_id, vbo_id FROM bag WHERE vbo_id IS NOT NULL;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.neighbourhood_vbo_ids = collections.defaultdict(list)
		for (buurt_id, vbo_id) in results:
			self.neighbourhood_vbo_ids[buurt_id].append(vbo_id)
		# Create dictionaries needed for storing information on relative electricity use and energy label >+ C
		self.neighbourhood_elec_check_dict = {}
		self.neighbourhood_energy_label_dict = {}
		cursor.close()

	def create_benchmark(self):
		# Create all possible combinations of characteristics
		building_type_tuple = ('Appartement', 'Hoekwoning', '2-onder-1-kapwoning', 'Tussenwoning', 'Vrijstaande woning')
		area_ranges_tuple = ('15 tot 50 m²', '50 tot 75 m²', '75 tot 100 m²', '100 tot 150 m²', '150 tot 250 m²', '250 tot 500 m²')
		household_size_tuple = ('1 persoon', '2 personen', '3 personen', '4 personen', '5 personen of meer')

		combination_tuple = list(itertools.product(building_type_tuple, area_ranges_tuple, household_size_tuple))
		self.elec_benchmark_dict = {}

		# Look up electricity use data for all possible building types
		for item in combination_tuple:
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
				self.elec_benchmark_dict[item] = interpolated_function

	def neighbourhood_elec_use_comparison(self,buurt_id):
		# Output: Dictionary with vbo_id:percentile electricity use
		percentile_elec_use_dict = {}
		connection = get_connection()
		# Get all dwellings in the neighbourhood
		sample = get_neighbourhood_dwellings(connection, buurt_id)

		for entry in sample:
			dwelling = Dwelling(dict(entry), connection)
			vbo_id = dwelling.attributes['vbo_id']

			# Electricity use in postal code
			postal_code = dwelling.attributes['pc6']
			postal_code_elec_use = self.postcode_elec_use_data.get(postal_code, 0)

			# Get dwellings attributes
			floor_space = dwelling.attributes['oppervlakte']
			building_type = dwelling.attributes['woningtype']
			household_size = round(self.postcode_household_size_data.get(postal_code,0))
			if household_size <= 0:
				household_size = 1
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
			benchmark = self.elec_benchmark_dict.get(dwelling_characteristics_tuple,0)

			# If there is not electricity use, we cannot compare
			if postal_code_elec_use == 0:
				pass
			# If there is not benchmark data, we cannot compare
			# TODO: set benchmark to more general data in def create_benchmark(self) if no data is available
			elif benchmark == 0:
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

	def neighbourhood_energy_labels(self, buurt_id):
		# Count the amount of dwellings that have an energy label of C or higher in a neighbourhood
		energy_labels_c_up = 0
		connection = get_connection()
		sample = get_neighbourhood_dwellings(connection, buurt_id)

		for entry in sample:
			dwelling = Dwelling(dict(entry), connection)
			vbo_id = dwelling.attributes['vbo_id']
			energy_label = energy_label = self.energy_label.get(vbo_id, 'Geen label')
			if energy_label == 'A+++' or energy_label == 'A++' or energy_label == 'A+' or energy_label == 'A' or energy_label == 'B' or energy_label == 'C':
				energy_labels_c_up += 1
		return energy_labels_c_up

	def process(self, dwelling):
		super().process(dwelling)

		# Get basic dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		buurt_id = dwelling.attributes['buurt_id']
		energy_label = dwelling.attributes['energy_label']

		# Base probability of having different types of electric heating
		hybrid_heat_pump_p = self.buurten_hybrid_heat_pump_data.get(buurt_id, 0) / 100
		elec_low_gas_p = self.buurten_elec_low_gas_data.get(buurt_id, 0) / 100
		elec_no_gas_p = self.buurten_elec_no_gas__data.get(buurt_id, 0) / 100
		# Placeholder electric boiler probability
		elec_boiler_p = elec_low_gas_p + elec_no_gas_p

		# Check if neighbourhood has already been through the electricity usage ranking process
		if buurt_id not in self.neighbourhood_elec_check_dict:
			# If not, add to the dictionary
			self.neighbourhood_elec_check_dict[buurt_id] = self.neighbourhood_elec_use_comparison(buurt_id)
		elec_use_percentile_national = self.neighbourhood_elec_check_dict[buurt_id][vbo_id]

		# Check electricty consumption percentile ranking within neighbourhood
<<<<<<< HEAD
		# Sort the electricity percentile ranking in the neighbourhood
		sorted_usage = sorted(self.neighbourhood_elec_check_dict[buurt_id][0].items(), key=lambda k_v: k_v[1][0])
		# Find the index of the dwelling in question
		index_list = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id]
		[index] = index_list
=======
		sorted_usage = list({k: v for k, v in sorted(self.neighbourhood_elec_check_dict[buurt_id].items(), key=lambda item: item[1])}.items())
		# Find the index of the dwelling in question
		index = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id].pop()
>>>>>>> heatpump
		# Calculate the ranking of the dwelling [0,1]
		elec_use_percentile_neighbourhood = (index+1)/len(sorted_usage)

<<<<<<< HEAD
		#Modify probabilities for heat pumps
=======
		# Modify probabilities for heat pumps
>>>>>>> heatpump
		# We assume there are only heat pumps in dwellings with energylabel C or higher
		if energy_label == 'A+++' or energy_label == 'A++' or energy_label == 'A+' or energy_label == 'A' or energy_label == 'B' or energy_label == 'C':
			# Check if the amount of dwellings with energylabel C or higher in the neighbourhood has been calculated
			if buurt_id not in self.neighbourhood_energy_label_dict:
				# If not, add to the dictionary
<<<<<<< HEAD
				self.neighbourhood_energy_label_dict[buurt_id].append(self.neighbourhood_energy_labels(buurt_id))
			[eligible_dwellings] = self.neighbourhood_energy_label_dict[buurt_id]
=======
				self.neighbourhood_energy_label_dict[buurt_id] = self.neighbourhood_energy_labels(buurt_id)
			eligible_dwellings = self.neighbourhood_energy_label_dict[buurt_id]
>>>>>>> heatpump

			# Probabilities are increased using new% = (old% * N_nbh)/(N_eligible)
			# Afterwards, probability is modified according to electricity use

			# Electric heat pump
<<<<<<< HEAD
			electric_heat_pump_p = 0.0155  * self.num_dwellings_in_neighbourhood[buurt_id])/eligible_dwellings # 0.0155 base percentage taken from WoON
=======
			electric_heat_pump_p = 0.0155  * self.num_dwellings_in_neighbourhood[buurt_id]/eligible_dwellings # 0.0155 base percentage taken from WoON
>>>>>>> heatpump
			electric_heat_pump_p = self.modify_probability(electric_heat_pump_p, elec_use_percentile_neighbourhood)

			# Hybrid heat pump
			hybrid_heat_pump_p = (hybrid_heat_pump_p * self.num_dwellings_in_neighbourhood[buurt_id])/eligible_dwellings
			hybrid_heat_pump_p = self.modify_probability(hybrid_heat_pump_p, elec_use_percentile_neighbourhood)
			# If there is a high electricity use we modify the probability of the hybrid heat pump according to the gas use
<<<<<<< HEAD
			if self.neighbourhood_elec_check_dict[buurt_id][vbo_id] > 0.7:
				hybrid_heat_pump_p = self.modify_probability(hybrid_heat_pump_p, gas_use_percentile_neighbourhood)
=======
			gas_use_percentile_national = dwelling.attributes['gas_use_percentile_national']
			if elec_use_percentile_national > 0.7:
				hybrid_heat_pump_p = self.modify_probability(hybrid_heat_pump_p, gas_use_percentile_national)
>>>>>>> heatpump
		else:
			electric_heat_pump_p = 0.
			hybrid_heat_pump_p = 0.

		# Modify probabilities for electric boiler
		elec_boiler_p = self.modify_probability(elec_boiler_p, elec_use_percentile_neighbourhood)

<<<<<<< HEAD
		dwelling.attributes['elec_use_percentile_neighbourhood'] = round(elec_use_percentile_neighbourhood,2)
		dwelling.attributes['electric_heat_pump_p'] = round(electric_heat_pump_p,2)
		dwelling.attributes['hybrid_heat_pump_p'] = round(hybrid_heat_pump_p,2)
		dwelling.attributes['elec_boiler_p'] = round(elec_boiler_p,2)
=======
		dwelling.attributes['elec_use_percentile_national'] = elec_use_percentile_national
		dwelling.attributes['elec_use_percentile_neighbourhood'] = elec_use_percentile_neighbourhood
		dwelling.attributes['electric_heat_pump_p'] = electric_heat_pump_p
		dwelling.attributes['hybrid_heat_pump_p'] = hybrid_heat_pump_p
		dwelling.attributes['elec_boiler_p'] = elec_boiler_p
>>>>>>> heatpump

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
