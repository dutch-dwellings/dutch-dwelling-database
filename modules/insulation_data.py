import copy
import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.probability_utils import ProbabilityDistribution

INSULATION_DATA = {

	# Based on the WoON survey 2018
	'dwelling_type_multipliers': {
		"hoekwoning": 1.07,
		"meergezinspand_hoog": 0.88,
		"meergezinspand_laag_midden": 0.88,
		"tussenwoning": 0.66,
		"twee_onder_1_kap": 0.83,
		"vrijstaand": 1.98
	},

	'building_code_r_values': {
		1992: {
			'facade': 2.5,
			'roof': 2.5,
			'wall': 2.5,
			'floor': 2.5,
			'window': 1/4.2
		},
		2003: { # no changes
			'facade': 2.5,
			'roof': 2.5,
			'wall': 2.5,
			'floor': 2.5,
			'window': 1/4.2
		},
		2012: {
			'facade': 3.5,
			'roof': 3.5,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/2.2
		},
		2013: {
			'facade': 3.5,
			'roof': 3.5,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/1.65
		},
		2014: { # no changes
			'facade': 3.5,
			'roof': 3.5,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/1.65
		},
		2015: {
			'facade': 4.5,
			'roof': 6,
			'wall': 3.5,
			'floor': 3.5,
			'window': 1/1.65
		},
		2021: {
			'facade': 4.7,
			'roof': 6.3,
			'wall': 3.7,
			'floor': 3.7,
			'window': 1/1.65
		}
	},

	# Data for average R-values for insulation
	# measures, from
	# https://www.rvo.nl/sites/default/files/2021/02/marktinformatie-isolatiematerialen-isolatiegas-en-hr-ketels-2010-2019.pdf.
	# Values for mineral and organic wool
	# for 2010-2012 have been corrected
	# to account for the different definition.
	'insulation_measures_r_values': {
		2010: ProbabilityDistribution([
				# (R-value, millions of m^2 sold)
				(2.4, 5.4), # synthetic insulation material
				(2.35, 10.1) # mineral and organic wools
			]),
		2011: ProbabilityDistribution([
				(2.5, 7.1),
				(2.46, 11.4)
			]),
		2012: ProbabilityDistribution([
				(2.7, 5.1),
				(2.57, 10.5)
			]),
		2013: ProbabilityDistribution([
				(2.8, 7.2),
				(2.9, 9.1)
			]),
		2014: ProbabilityDistribution([
				(2.7, 9.2),
				(2.8, 10.1)
			]),
		2015: ProbabilityDistribution([
				(3.3, 11.1),
				(2.8, 12)
			]),
		2016: ProbabilityDistribution([
				(3.3, 15.3),
				(3, 13.9)
			]),
		2017: ProbabilityDistribution([
				(2.8, 15.4),
				(3, 14.2)
			]),
		2018: ProbabilityDistribution([
				(2.9, 11.4),
				(3.4, 14.5)
			]),
		2019: ProbabilityDistribution([
				(3.3, 10.2),
				(3.8, 11.8)
			])
	},

	# https://energiecijfers.databank.nl/dashboard/dashboard/energiebesparing/
	'insulation_measures_n': {
		2010: {
			'facade': 35838,
			'roof': 115398,
			'window': 209353,
			'cavity wall': 76784,
			'floor': 65807,
		},
		2011: {
			'facade': 73097,
			'roof': 157347,
			'window': 295286,
			'cavity wall': 114914,
			'floor': 122313,
		},
		2012: {
			'facade': 76480,
			'roof': 195420,
			'window': 357411,
			'cavity wall': 117197,
			'floor': 130465,
		},
		2013: {
			'facade': 60548,
			'roof': 124267,
			'window': 215387,
			'cavity wall': 96150,
			'floor': 106162,
		},
		2014: {
			'facade': 84501,
			'roof': 155099,
			'window': 266949,
			'cavity wall': 131324,
			'floor': 138444,
		},
		2015: {
			'facade': 74448,
			'roof': 148447,
			'window': 265195,
			'cavity wall': 132769,
			'floor': 150615,
		},
		2016: {
			'facade': 75802,
			'roof': 148100,
			'window': 261522,
			'cavity wall': 159507,
			'floor': 146108,
		},
		2017: {
			'facade': 85442,
			'roof': 164024,
			'window': 259146,
			'cavity wall': 159080,
			'floor': 164511,
		},
		2018: {
			'facade': 100978,
			'roof': 199784,
			'window': 312337,
			'cavity wall': 214035,
			'floor': 204460,
		},
		2019: {
			'facade': 125197,
			'roof': 246325,
			'window': 376869,
			'cavity wall': 281276,
			'floor': 238257,
		}
	},

	# Number of dwellings built in or before a certain
	# construction year.
	# Based on the BAG from 2021, without demolished buildings,
	# so this misses some demolished buildings
	'dwellings_n': {
		1919: 605351,
		1974: 3878416,
		2000: 6591218,
		2001: 6669286,
		2002: 6739330,
		2003: 6804459,
		2004: 6870704,
		2005: 6943943,
		2006: 7027060,
		2007: 7109692,
		2008: 7189902,
		2009: 7261671,
		2021: 7892928 # total
	},

	# Based on the WoON survey 2006
	'base_r_values_1992_2005': {
		'vrijstaand': {
			'facade': ProbabilityDistribution({
					2.53: 0.532,
					2.86: 0.468
				}),
			'roof': ProbabilityDistribution({
					2.53: 0.967,
					2.72: 0.033
				}),
			'floor': ProbabilityDistribution({
					2.53: 0.983,
					2.65: 0.017
				})
		},
		# Same for 'hoekwoning'
		'twee_onder_1_kap': {
			'facade': ProbabilityDistribution({
					2.53: 0.538,
					2.86: 0.462
				}),
			'roof': ProbabilityDistribution({
					2.53: 0.945,
					2.72: 0.055
				}),
			'floor': ProbabilityDistribution({
					2.53: 0.951,
					2.65: 0.049
				})
		},
		'tussenwoning': {
			'facade': ProbabilityDistribution({
					2.53: 0.572,
					2.86: 0.428
				}),
			'roof': ProbabilityDistribution({
					2.53: 0.915,
					2.72: 0.085
				}),
			'floor': ProbabilityDistribution({
					2.53: 0.976,
					2.65: 0.024
				})
		},
		# Same for meergezinspand_laag_midden
		'meergezinspand_hoog': {
			'facade': ProbabilityDistribution({
					2.53: 0.818,
					2.86: 0.182
				}),
			'roof': ProbabilityDistribution({
					2.53: 0.962,
					2.72: 0.038
				}),
			'floor': ProbabilityDistribution({
					2.53: 0.985,
					2.65: 0.015
				})
		}
	},

	# Based on the WoON survey 2006
	'base_r_values_1920_1991': {
		'vrijstaand': {
			'facade': ProbabilityDistribution({
					0.43: 0.000,
					1.30: 0.000,
					1.36: 0.000,
					2.11: 0.548,
					2.53: 0.240,
					2.86: 0.212
				}),
			'roof': ProbabilityDistribution({
					0.22: 0.000,
					0.39: 0.025,
					0.86: 0.017,
					0.97: 0.302,
					1.22: 0.070,
					1.30: 0.185,
					1.97: 0.237,
					2.00: 0.107,
					2.53: 0.054,
					2.72: 0.002
				}),
			'floor': ProbabilityDistribution({
					0.15: 0.006,
					0.17: 0.116,
					0.32: 0.108,
					0.52: 0.116,
					0.65: 0.166,
					1.30: 0.058,
					1.40: 0.052,
					2.00: 0.116,
					2.15: 0.160,
					2.53: 0.099,
					2.65: 0.002
				})
			},
		# Same for 'hoekwoning'
		'twee_onder_1_kap': {
			'facade': ProbabilityDistribution({
					0.43: 0.040,
					1.30: 0.022,
					1.36: 0.000,
					2.11: 0.690,
					2.53: 0.134,
					2.86: 0.115
				}),
			'roof': ProbabilityDistribution({
					0.22: 0.000,
					0.39: 0.021,
					0.86: 0.060,
					0.97: 0.272,
					1.22: 0.048,
					1.30: 0.257,
					1.97: 0.196,
					2.00: 0.110,
					2.53: 0.034,
					2.72: 0.002
				}),
			'floor': ProbabilityDistribution({
					0.15: 0.004,
					0.17: 0.209,
					0.32: 0.095,
					0.52: 0.134,
					0.65: 0.123,
					1.30: 0.132,
					1.40: 0.022,
					2.00: 0.125,
					2.15: 0.089,
					2.53: 0.064,
					2.65: 0.003
				})
			},
		'tussenwoning': {
			'facade': ProbabilityDistribution({
					0.43: 0.922,
					1.30: 0.042,
					1.36: 0.002,
					2.11: 0.674,
					2.53: 0.109,
					2.86: 0.082
				}),
			'roof': ProbabilityDistribution({
					0.22: 0.002,
					0.39: 0.028,
					0.86: 0.070,
					0.97: 0.266,
					1.22: 0.038,
					1.30: 0.326,
					1.97: 0.172,
					2.00: 0.084,
					2.53: 0.012,
					2.72: 0.001
				}),
			'floor': ProbabilityDistribution({
					0.15: 0.006,
					0.17: 0.253,
					0.32: 0.092,
					0.52: 0.174,
					0.65: 0.104,
					1.30: 0.161,
					1.40: 0.014,
					2.00: 0.099,
					2.15: 0.062,
					2.53: 0.035,
					2.65: 0.001
				})
			},
		# Same for meergezinspand_laag_midden
		'meergezinspand_hoog': {
			'facade': ProbabilityDistribution({
					0.43: 0.000,
					1.30: 0.021,
					1.36: 0.000,
					2.11: 0.554,
					2.53: 0.347,
					2.86: 0.077
				}),
			'roof': ProbabilityDistribution({
					0.22: 0.004,
					0.39: 0.020,
					0.86: 0.125,
					0.97: 0.214,
					1.22: 0.032,
					1.30: 0.270,
					1.97: 0.125,
					2.00: 0.113,
					2.53: 0.094,
					2.72: 0.004
				}),
			'floor': ProbabilityDistribution({
					0.15: 0.006,
					0.17: 0.176,
					0.32: 0.065,
					0.52: 0.182,
					0.65: 0.047,
					1.30: 0.206,
					1.40: 0.018,
					2.00: 0.082,
					2.15: 0.047,
					2.53: 0.169,
					2.65: 0.003
				})
			}
	},

	'glazing_r_values': {
		'single': ProbabilityDistribution({0.175: 1}),
		'double': ProbabilityDistribution({0.333: 1}),
		'hr': ProbabilityDistribution({(0.5, 0.625): 1}),
		'hr+': ProbabilityDistribution({(0.625, 0.833): 1}),
		'hr++': ProbabilityDistribution({0.833: 1})
	},

	'cavity_wall_r_value': ProbabilityDistribution({(1.25, 2.175): 1})
}

# WoON survey 2006 only had 4 categories,
# we extend it to the current 6 categories.
INSULATION_DATA['base_r_values_1992_2005']['hoekwoning'] = INSULATION_DATA['base_r_values_1992_2005']['twee_onder_1_kap']
INSULATION_DATA['base_r_values_1992_2005']['meergezinspand_laag_midden'] = INSULATION_DATA['base_r_values_1992_2005']['meergezinspand_hoog']

INSULATION_DATA['base_r_values_1920_1991']['hoekwoning'] = INSULATION_DATA['base_r_values_1920_1991']['twee_onder_1_kap']
INSULATION_DATA['base_r_values_1920_1991']['meergezinspand_laag_midden'] = INSULATION_DATA['base_r_values_1920_1991']['meergezinspand_hoog']

# The data for before 1920 is almost the same,
# except buildings before 1920 rarely have cavity walls,
# therefor the facade insulation is worse.
# We change only that part.
# We need to deepcopy since we are going to change some values,
# and we don't want them to end up in the 'base_r_values_1920_1991'.
INSULATION_DATA['base_r_values_before_1920'] = copy.deepcopy(INSULATION_DATA['base_r_values_1920_1991'])
INSULATION_DATA['base_r_values_before_1920']['vrijstaand']['facade'] = ProbabilityDistribution({
		0.36: 0.018,
		0.43: 0.469,
		1.30: 0.197,
		1.36: 0.000,
		2.11: 0.315
	})
# automatically copies to 'hoekwoning'
INSULATION_DATA['base_r_values_before_1920']['twee_onder_1_kap']['facade'] = ProbabilityDistribution({
		0.43: 1
	})
INSULATION_DATA['base_r_values_before_1920']['tussenwoning']['facade'] = ProbabilityDistribution({
		0.43: 1
	})
# automatically copies to 'meergezinspand_laag_midden'
INSULATION_DATA['base_r_values_before_1920']['meergezinspand_hoog']['facade'] = ProbabilityDistribution({
		0.43: 0.971,
		1.30: 0.029
	})
