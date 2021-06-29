import os
import sys

import numpy as np
from psycopg2.extras import NumericRange

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))

from base_module import BaseModule, BaseRegionalModule
from utils.energy_label_utils import epi_to_label

class EnergyLabelModule(BaseModule):

	def get_energy_label(self, vbo_id):
		cursor = self.connection.cursor()
		# Get energy label of dwelling
		query = "SELECT energieklasse FROM energy_labels WHERE energieklasse IS NOT null AND vbo_id = %s"
		cursor.execute(query, (vbo_id,))
		results = cursor.fetchone()
		if results is not None:
			results = results[0]
		return results
		cursor.close()

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		vbo_id = dwelling.attributes['vbo_id']
		energy_label = self.get_energy_label(vbo_id)
		dwelling.attributes['energy_label'] = energy_label

class EnergyLabelPredictionModule(BaseModule):

	def predict_epi(self, dwelling):
		'''
		Predict the EPI (EnergiePrestatieIndex)
		of the dwelling using multiple linear
		regression, on the basis of dwelling type,
		construction year, and the average log(epi)
		in the pc6.
		'''

		beta = self.regression_values['beta']
		S = self.regression_values['S']
		s_2 = self.regression_values['s_2']
		t_multiplier = self.regression_values['t_multiplier']
		calibration_factor = self.regression_values['calibration_factor']

		dwelling_type = dwelling.attributes['woningtype']
		construction_year = dwelling.attributes['bouwjaar']
		pc6 = dwelling.regions['pc6']

		x = np.array([
			1, # intercept
			1 if dwelling_type == 'meergezinspand_hoog' else 0,
			1 if dwelling_type == 'meergezinspand_laag_midden' else 0,
			1 if dwelling_type == 'tussenwoning' else 0,
			1 if dwelling_type == 'twee_onder_1_kap' else 0,
			1 if dwelling_type == 'vrijstaand' else 0,
			max(construction_year, 1900),
			pc6.attributes['epi_log_pc6_average']
		])

		y_hat = np.dot(beta, x)

		half_interval_size = calibration_factor * t_multiplier * np.sqrt(s_2 + x @ S @ x)
		# 95% Prediction Interval for log(epi)
		PI_min = y_hat - half_interval_size
		PI_max = y_hat + half_interval_size
		# 95% Prediction Interval for log(epi)
		PI = (np.exp(PI_min), np.exp(PI_max))

		return np.exp(y_hat), PI

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		prediction, prediction_interval = self.predict_epi(dwelling)
		dwelling.attributes['energy_label_epi_mean'] = prediction
		dwelling.attributes['energy_label_epi_95'] = NumericRange(prediction_interval[0], prediction_interval[1], bounds='[]')
		dwelling.attributes['energy_label_class_mean'] = epi_to_label(prediction)
		dwelling.attributes['energy_label_class_95'] = (epi_to_label(prediction_interval[0]), epi_to_label(prediction_interval[1]))

	# Coefficients for the multiple linear regression
	# as applied in predict_epi()
	regression_values = {

		'beta': np.array([
			 3.845226, # intercept
			-0.023008, # meergezinspand_hoog
			-0.032551, # meergezinspand_laag_midden
			-0.030663, # tussenwoning
			-0.004443, # twee_onder_1_kap
			-0.014757, # vrijstaand
			-0.001914, # max(bouwjaar, 1900)
			 0.869052  # epi_log_pc6_average
		]),

		'S': np.array([
			[ 6.83876309e-05, -4.00281547e-08, -4.96759316e-08, -8.97807500e-08,
			 -1.04731190e-07, -7.91791170e-08, -3.42128022e-08, -2.32398014e-06],
			[-4.00281547e-08,  9.98566604e-08,  6.23615411e-08, 6.23514842e-08,
			  6.26976117e-08,  6.28056443e-08, -1.05324239e-11, -4.96071168e-09],
			[-4.96759316e-08,  6.23615411e-08,  9.86977618e-08,  6.24197768e-08,
			  6.23149562e-08,  6.22907493e-08, -6.57281481e-12,  7.87520979e-10],
			[-8.97807500e-08,  6.23514842e-08,  6.24197768e-08,  8.91604438e-08,
			  6.23448849e-08,  6.23073636e-08,  1.35204628e-11,  2.08067097e-09],
			[-1.04731190e-07,  6.26976117e-08,  6.23149562e-08,  6.23448849e-08,
			  1.78080611e-07,  6.30826024e-08,  2.23064301e-11, -5.49561405e-09],
			[-7.91791170e-08,  6.28056443e-08,  6.22907493e-08,  6.23073636e-08,
			  6.30826024e-08,  1.64436238e-07,  9.88064924e-12, -8.66014735e-09],
			[-3.42128022e-08, -1.05324239e-11, -6.57281481e-12,  1.35204628e-11,
			  2.23064301e-11,  9.88064924e-12,  1.71340338e-11,  1.14814781e-09],
			[-2.32398014e-06, -4.96071168e-09,  7.87520979e-10,  2.08067097e-09,
			 -5.49561405e-09, -8.66014735e-09,  1.14814781e-09,  1.75767544e-07]
		]),

		's_2': 0.0345167406307920,

		# Can be calculated with
		#	scipy.stats.t.ppf(1 - alpha / 2, deg_f)
		# with alpha = 0.05, deg_f > 4M.
		't_multiplier': 1.9599645281714109,

		# Empirically determined to get 95% of
		# prediction rights on Energy Label
		# data set.
		'calibration_factor': 1.1435939114804017
	}

	outputs = {
		'energy_label_epi_mean': {
			'type': 'double precision'
		},
		'energy_label_epi_95': {
			'type': 'numrange'
		},
		'energy_label_class_mean': {
			'type': 'energy_label_class'
		},
		'energy_label_class_95': {
			'type': 'text'
		}
	}

class EnergyLabelRegionalModule(BaseRegionalModule):

	def process_pc6(self, pc6):
		epi_log_pc6_average_query = "SELECT AVG(LN(epi_imputed)) FROM energy_labels WHERE pc6 = %s AND epi_imputed > 0"
		cursor = self.connection.cursor()
		pc6_code = pc6.attributes['pc6']
		cursor.execute(epi_log_pc6_average_query, (pc6_code,))
		pc6.attributes['epi_log_pc6_average'] = cursor.fetchone()[0]
		cursor.close()

	supports = ['pc6']
