import os
import sys

import pandas as pd

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

from utils.probability_utils import ProbabilityDistribution
from modules.insulation_data import INSULATION_DATA

class InsulationModule(BaseModule):

	# Types:
	# - roof insulation
	# - facade insulation (with and without cavity wall)
	# - floor insulation
	# - window insulation
	# - wall insulation

	def __init__(self, connection, **kwargs):
		super().__init__(self, **kwargs)
		self.dwelling_type_multipliers = INSULATION_DATA['dwelling_type_multipliers']
		self.building_code_r_values = self.year_dict_to_dataframe(INSULATION_DATA['building_code_r_values'])
		self.insulation_measures_r_values = INSULATION_DATA['insulation_measures_r_values']
		self.insulation_measures_n = INSULATION_DATA['insulation_measures_n']
		self.dwellings_n = INSULATION_DATA['dwellings_n']
		self.base_r_values_1992_2005 = INSULATION_DATA['base_r_values_1992_2005']
		self.base_r_values_1920_1991 = INSULATION_DATA['base_r_values_1920_1991']
		self.base_r_values_before_1920 = INSULATION_DATA['base_r_values_before_1920']

	def year_dict_to_dataframe(self, dict):
		'''
		Convert a dict of the form
		{
			year_1: {
				cat1: value1,
				cat2: value2,
				...
			},
			...
		}
		into a Pandas DataFrame
			year	cat1	cat2	...
		0	year_1	value1	value2	...
		...
		'''
		df = pd.DataFrame.from_dict(dict, orient='index')

		# Convert the year-index to a seperate column 'year'.
		df.index.rename('year', inplace=True)
		df.reset_index(inplace=True)

		return df

	def process(self, dwelling):
		self.process_facade(dwelling)

	def get_building_code(self, construction_year):
		'''
		Get the building code applicable to buildings
		built in 'construction_year'. Only works for
		buildings built in or after 1992.
		'''
		df = self.building_code_r_values
		# Get the most recent version up to the the construction year.
		return df[df.year <= construction_year].iloc[-1]

	def process_facade(self, dwelling):
		construction_year = dwelling.attributes['bouwjaar']
		dwelling_type = dwelling.attributes['woningtype']

		# From 2006 onwards, we don't have the WoON
		# base distribution anymore,
		# so we use the building code.
		if construction_year >= 2006:
			building_code = self.get_building_code(construction_year)
			facade_r = building_code['facade']
			facade_base_dist = ProbabilityDistribution({facade_r: 1})
		# From 1992 onwards, we have the WoON distribution
		# that we modified so it matches the building code.
		elif construction_year >= 1992:
			facade_base_dist = self.base_r_values_1992_2005[dwelling_type]['facade']
		# Cutoff point: buildings from 1920 (usually) have cavity walls, so we modified the WoON base distributions for that.
		elif construction_year >= 1920:
			facade_base_dist = self.base_r_values_1920_1991[dwelling_type]['facade']
		else:
			facade_base_dist = self.base_r_values_before_1920[dwelling_type]['facade']

		# We only have data available for 2010 to 2019,
		# and we assume a waiting period of
		# MIN_YEAR_MEASURE_AFTER_CONSTRUCTION
		# after construction before a measure gets taken.
		applicable_measure_years = range(max(2010, construction_year + self.MIN_YEAR_MEASURE_AFTER_CONSTRUCTION), 2019 + 1)

		measures_r_values = [
			self.insulation_measures_r_values[year]
			for year
			in applicable_measure_years
		]

		measure_prob_multiplier = self.dwelling_type_multipliers[dwelling_type]
		facade_measures_prob = [
			# Calculate probability of a measure being taken for this dwelling in 'year':
			# number of insulation measures divided by number of dwellings that
			# could have taken the measure, multiplied by the dwelling type multiplier.
			measure_prob_multiplier \
			* self.insulation_measures_n[year]['facade'] \
			/ self.dwellings_n[year - self.MIN_YEAR_MEASURE_AFTER_CONSTRUCTION]
			for year
			in applicable_measure_years
		]

		if len(applicable_measure_years) == 0:
			facade_measures_dist = ProbabilityDistribution({
					0: 1
				})
		else:
			facade_measures_dist = sum([
					measures_r_values[i] * facade_measures_prob[i]
					for i in range(len(measures_r_values))
				])
			facade_measures_dist.pad()

		# Add the increase of R-values in facade_measures_dist
		# to the base distribution facade_base_dist.
		insulation_facade_r_dist = facade_base_dist & facade_measures_dist

		dwelling.attributes['insulation_facade_r_dist'] = insulation_facade_r_dist

	# We assume no insulation measures will be taken
	# in the first 10 years after construction.
	# Maybe this should be higher?
	MIN_YEAR_MEASURE_AFTER_CONSTRUCTION = 10
