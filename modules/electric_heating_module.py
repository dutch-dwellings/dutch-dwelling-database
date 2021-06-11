import os
import sys
from scipy.interpolate import interp1d
import itertools
import math

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
		self.create_benchmark()

	def load_installation_type_data(self):
		# create dictionary with buurt_id and percentage of gas boilers
		cursor = self.connection.cursor()
		query = '''
		SELECT wijken_en_buurten, SUM(woningen) as woningen
		FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019
		WHERE (wijken_en_buurten LIKE 'BU%')
		AND (type_verwarmingsinstallatie LIKE 'A050117'
		OR type_verwarmingsinstallatie LIKE 'A050118'
		OR type_verwarmingsinstallatie LIKE 'A050119')
		AND woningen IS NOT null
		GROUP BY wijken_en_buurten;
		'''
		cursor.execute(query)
		results = cursor.fetchall()
		self.buurten_verwarming_data = {
		buurt_id: percentage_elec_heating
		for (buurt_id, percentage_elec_heating)
		in results
		}
		cursor.close()

	def load_elec_use_data(self):
		# Create dictionary which relates the postal code of a dwelling and the electricity use of that postal code
		cursor = self.connection.cursor()
		query = "SELECT postcode6, gemiddelde_elektriciteitslevering_woningen FROM cbs_pc6_2019_energy_use WHERE gemiddelde_elektriciteitslevering_woningen IS NOT NULL;"
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

	def create_benchmark(self):
		# This is a holdover from another approach. Could be useful to maybe increase efficiency by first interpolating the benchmarks and only comparing the gas use per square meter in the process function.
		building_type_tuple = ('Appartement', 'Hoekwoning', '2-onder-1-kapwoning', 'Tussenwoning', 'Vrijstaande woning')
		area_ranges_tuple = ('15 tot 50 m²', '50 tot 75 m²', '75 tot 100 m²', '100 tot 150 m²', '150 tot 250 m²', '250 tot 500 m²')
		household_size_tuple = ('1 persoon', '2 personen', '3 personen', '4 personen', '5 personen of meer')

		combination_tuple = list(itertools.product(building_type_tuple, area_ranges_tuple, household_size_tuple))
		self.elec_benchmark_dict = {}

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
			results = cursor.fetchall()
			benchmark_y_data = [5, 25, 50, 75, 95]
			benchmark_x_data = [x for x in results]
			benchmark_x_data = list(sum(benchmark_x_data, ()))
			if None in benchmark_x_data or benchmark_x_data == []:
				pass
			# Interpolate the data, with extrapolation for <5 and >95 percentile
			else:
				if benchmark_x_data[3] == benchmark_x_data[4]:
					benchmark_x_data[4] == benchmark_x_data[4] + 0.1

				interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
				self.elec_benchmark_dict[item]=interpolated_function

	def process(self, dwelling):
		super().process(dwelling)

		# Base probability of having electric heating
		buurt_id = dwelling.attributes['buurt_id']
		elec_heating_p_base = self.buurten_verwarming_data.get(buurt_id, 0) / 100

		# Electricity use in postal code
		postal_code = dwelling.attributes['postcode']
		postal_code_elec_use = self.postcode_elec_use_data.get(postal_code, 0)

		# Get dwellings attributes
		bag_id = dwelling.attributes['identificatie']
		floor_space = dwelling.attributes['oppervlakte']
		building_type = dwelling.attributes['woningtype']
		household_size = round(self.postcode_household_size_data.get(postal_code,0))
		if household_size <= 0:
			household_size =1

		# Get electricity use per person for comparison
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
			# There are 51474 dwellings in the BAG that do not have a building type assigned. These are demolished buildings.
		else:
			building_type = ''

		# Make areas searchable
		if floor_space < 50:
			floor_space_string = '15 tot 50 m²'
		elif floor_space >= 50 and floor_space <75:
			floor_space_string = '50 tot 75 m²'
		elif floor_space >= 75 and floor_space <100:
			floor_space_string = '75 tot 100 m²'
		elif floor_space >= 100 and floor_space<150:
			floor_space_string = '100 tot 150 m²'
		elif floor_space >= 150 and floor_space<250:
			floor_space_string = '150 tot 250 m²'
		elif floor_space >=250:
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

		benchmark = self.elec_benchmark_dict.get(dwelling_characteristics_tuple,0)

		# If there is not gas use, we cannot compare
		if postal_code_elec_use == 0 or benchmark == 0:
			#print('No gas use to compare')
			pass
		else:
			dwelling_elec_use_percentile = float( benchmark(dwelling_elec_use_per_person))
			# Extrapolation can give values outside of the domain
			if dwelling_elec_use_percentile < 0:
				dwelling_elec_use_percentile = 0
			elif dwelling_elec_use_percentile > 100:
				dwelling_elec_use_percentile = 100
			else:
				pass
		dwelling_elec_use_percentile = round(dwelling_elec_use_percentile,2)
		dwelling.attributes['dwelling_elec_use_percentile'] = dwelling_elec_use_percentile

	outputs = {
		'dwelling_elec_use_percentile': {
			'type': 'double precision'
		}
	}
