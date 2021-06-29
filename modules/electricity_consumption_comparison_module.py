import os
import sys
from scipy.interpolate import interp1d

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule, BaseRegionalModule
from classes import Dwelling

class ElectricityConsumptionComparisonModule(BaseModule):

	def __init__(self, connection, **kwargs):
		super().__init__(connection, **kwargs)
		self.elec_benchmark_dict = {}

	def neighbourhood_elec_use_comparison(self, buurt, pc6):
		# Create dictionary with vbo_ids : percentile of gas users
		percentile_elec_use_dict = {}
		# Get dwellings in neighbourhood
		dwellings_in_neighbourhood = buurt.dwellings
		# Total electricity use in postal code
		postal_code_elec_use = pc6.attributes['total_elec_use']
		# Total floor space in postal code
		postal_code_floor_space = pc6.attributes['total_floor_space']
		# Assumption: Electricity use per m2 is the same for the entire pc6
		elec_use_floor_space = postal_code_elec_use / postal_code_floor_space
		# Household size of dwelling
		avg_household_size = round(pc6.attributes['household_size'])
		if avg_household_size <= 0:
			avg_household_size = 1

		# Comparison process
		for dwelling in dwellings_in_neighbourhood:
			# Get basic attributes
			vbo_id = dwelling.attributes['vbo_id']
			floor_space = dwelling.attributes['oppervlakte']
			dwelling.attributes['household_size'] = avg_household_size

			# Electricity use of a dwelling
			elec_use_dwelling = elec_use_floor_space * floor_space
			# Get electricity use per person for comparison with benchmark
			dwelling_elec_use_per_person = elec_use_dwelling / avg_household_size
			dwelling_elec_use_percentile = 0

			# Create tuple for looking up benchmark
			dwelling_characteristics_tuple = self.create_characteristics_tuple(dwelling)
			# Check if benchmark for combination of characteristics is already made
			if dwelling_characteristics_tuple not in self.elec_benchmark_dict:
				# If not, calculate the benchmark function
				self.elec_benchmark_dict[dwelling_characteristics_tuple] = self.create_benchmark(dwelling_characteristics_tuple)

			# Comparison with benchmark
			benchmark = self.elec_benchmark_dict[dwelling_characteristics_tuple]

			# If there is not electricity use, we cannot compare
			if postal_code_elec_use == 0:
				pass
			# If there is not benchmark data, we cannot compare
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
			# Add percentile compared to national data to dict
			percentile_elec_use_dict[vbo_id] = dwelling_elec_use_percentile

		return(percentile_elec_use_dict)

	def create_characteristics_tuple(self, dwelling):
		# Get dwellings attributes
		floor_space = dwelling.attributes['oppervlakte']
		building_type = dwelling.attributes['woningtype']
		energy_label = dwelling.attributes['energy_label_class']
		household_size = dwelling.attributes['household_size']

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

		dwelling_characteristics_tuple = (building_type, floor_space_string, household_size_string)

		return dwelling_characteristics_tuple

	def create_benchmark(self, dwelling_characteristics_tuple):
		# Look up electricity use data for dwellings characteristics
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
		cursor.execute(query_statement, dwelling_characteristics_tuple)
		# Interpolate the data, with extrapolation for <5 and >95 percentile
		results = cursor.fetchall()
		benchmark_y_data = [5, 25, 50, 75, 95]
		benchmark_x_data = [x for x in results]
		benchmark_x_data = list(sum(benchmark_x_data, ()))
		if None in benchmark_x_data or benchmark_x_data == []:
			# Need to find a way to make this have results. Query for totaal? How to find the characteristic that is the culprit?
			interpolated_function = 0
		else:
			interpolated_function = interp1d(benchmark_x_data, benchmark_y_data, fill_value='extrapolate')
		return interpolated_function

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		# Get dwelling attributes
		vbo_id = dwelling.attributes['vbo_id']
		pc6 = dwelling.regions['pc6']
		buurt = dwelling.regions['buurt']

		# Check if neighbourhood has already been through the electricity usage ranking process
		if vbo_id not in buurt.elec_use:
			# If not, add to the dictionary
			buurt.elec_use = self.neighbourhood_elec_use_comparison(buurt, pc6)

		# Check electricty consumption percentile ranking within neighbourhood
		sorted_usage = list({k: v for k, v in sorted(buurt.elec_use.items(), key=lambda item: item[1])}.items())
		# Find the index of the dwelling in question
		index = [i for i, tupl in enumerate(sorted_usage) if tupl[0] == vbo_id].pop()
		# Calculate the ranking of the dwelling [0,1]
		elec_use_percentile_neighbourhood = (index+1)/len(sorted_usage)

		dwelling.attributes['elec_use_percentile_national'] = buurt.elec_use[vbo_id]
		dwelling.attributes['elec_use_percentile_neighbourhood'] = elec_use_percentile_neighbourhood

class ElectricityConsumptionComparisonRegionalModule(BaseRegionalModule):

	def process_pc6(self, pc6):
		self.load_elec_use_data(pc6)
		self.load_cbs_kerncijfers_data(pc6)

	def load_elec_use_data(self, pc6):
		# Compute
		cursor = self.connection.cursor()
		query = '''
		SELECT gemiddelde_elektriciteitslevering_woningen
		FROM cbs_pc6_2019_energy_use
		WHERE
			gemiddelde_elektriciteitslevering_woningen IS NOT NULL
			AND pc6 = %s'''
		cursor.execute(query, (pc6.attributes['pc6'],))
		avg_electricity_use = cursor.fetchone()
		avg_electricity_use = self.handle_null_data(avg_electricity_use)
		number_of_dwellings = pc6.attributes['number_of_dwellings']
		pc6.attributes['total_elec_use'] = avg_electricity_use * number_of_dwellings
		cursor.close()

	def load_cbs_kerncijfers_data(self, pc6):
		# Add average pc6 household size to dict
		cursor = self.connection.cursor()
		query = '''
		SELECT gem_hh_gr
		FROM cbs_pc6_2017_kerncijfers
		WHERE
			gem_hh_gr IS NOT null
			AND pc6 = %s'''
		cursor.execute(query, (pc6.attributes['pc6'],))
		household_size = cursor.fetchone()
		household_size = self.handle_null_data(household_size)
		pc6.attributes['household_size'] = household_size
		cursor.close()

	supports = ['pc6']
