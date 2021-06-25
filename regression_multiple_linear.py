import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.predstd import wls_prediction_std

from utils.database_utils import get_connection

def get_energy_labels():
	print('### energy labels ###')
	print('Getting results...')
	connection = get_connection()
	cursor = connection.cursor()
	query = '''
	SELECT
		epi_imputed,
		bag.bouwjaar,
		q.epi_pc6_average,
		r.epi_inv_pc6_average,
		s.epi_log_pc6_average,
		bag.woningtype,
		bag.oppervlakte,
		bag.nr_verdiepingen
	FROM
		energy_labels,
		bag,
		(SELECT pc6, AVG(epi_imputed) as epi_pc6_average FROM energy_labels WHERE epi_imputed > 0 GROUP BY pc6) q,
		(SELECT pc6, AVG(1/epi_imputed) as epi_inv_pc6_average FROM energy_labels WHERE epi_imputed > 0 GROUP BY pc6) r,
		(SELECT pc6, AVG(LN(epi_imputed)) as epi_log_pc6_average FROM energy_labels WHERE epi_imputed > 0 GROUP BY pc6) s
	WHERE
		energy_labels.vbo_id = bag.vbo_id
		AND energieklasse IS NOT NULL
		AND q.pc6 = bag.pc6
		AND r.pc6 = bag.pc6
		AND s.pc6 = bag.pc6
		AND epi_imputed > 0
	'''
	cursor.execute(query)
	results = cursor.fetchall()

	print('Converting to dataframe...')
	df = pd.DataFrame(results, columns=['epi_imputed', 'bouwjaar', 'epi_pc6_average', 'epi_inv_pc6_average', 'epi_log_pc6_average', 'woningtype', 'oppervlakte', 'nr_verdiepingen'])
	return df

def multiple_linear_regression(df, formula):
	print("\n=== multiple linear regression ===")
	print(f'formula: {formula}')
	result = smf.ols(formula=formula, data=df).fit()
	return result

def get_regression_values(result):
	beta = result.params
	s_2 = result.mse_resid
	var_covar_matrix = result.cov_params()

	return beta, s_2, var_covar_matrix

def process_regression_result(result, alpha=0.05):
	print('\n--- processing regression results ---')

	print(f'beta:\n{result.params}')


	print(f'\nalpha: {alpha}')

	x_h = {
		'bouwjaar': 2020,
		'epi_pc6_average': 1.2, # B average
		'epi_inv_pc6_average': 0.8333333333,
		'epi_log_pc6_average': 0.1823215568,
		'woningtype': 'tussenwoning',
		'oppervlakte': 117, # average
		'nr_verdiepingen': 3 # modus
	}
	prediction = result.get_prediction(x_h)

	y_h_hat = prediction.predicted_mean[0]
	print(f'y_h_hat: {y_h_hat}')
	frame = prediction.summary_frame(alpha=alpha)
	PI_range_max = float(frame.obs_ci_upper)
	PI_range_min = float(frame.obs_ci_lower)
	PI_range = (PI_range_min, PI_range_max)
	print(f'PI_range: {PI_range}')

	s_2 = result.mse_resid
	print(f's_2: {s_2}')
	print(f's: {np.sqrt(s_2)}')

	R_2 = result.rsquared
	print(f'R_2: {R_2}')

	prstd, iv_l, iv_u = wls_prediction_std(result, alpha=alpha)
	# These values are not the original epi_imputed,
	# but have already been modified by Patsy to e.g. 1/epi_imputed
	# or log(epi_imputed) where applicable.
	y = result.model.data.endog
	# Number of right predictions, where the true y-value
	# falls within the lower and upper prediction ranges.
	hits = ((iv_l < y) & (y < iv_u)).sum()
	print(f'correct predictions: {hits/len(y)*100}%')

	n = len(y)
	p = len(result.model.data.exog[0])
	deg_f = n - p

	t_multiplier = stats.t.ppf(1-alpha/2, deg_f)
	t_multiplier_5 = stats.t.ppf(1-0.05/2, deg_f)
	print(f'\nt_multiplier: {t_multiplier}')
	print(f'ratio to alpha=0.05: {t_multiplier/t_multiplier_5}')

def compare_formulas(df):
	formulas = [
		# automatically codes 'woningtype'
		'epi_imputed ~ bouwjaar + epi_pc6_average + woningtype'
		# add oppervlakte, n_verdiepingen
		'epi_imputed ~ bouwjaar + epi_pc6_average + woningtype + oppervlakte + nr_verdiepingen'
		# cutoff building year at 1900
		'epi_imputed ~ np.maximum(bouwjaar, 1900) + epi_pc6_average + woningtype'
		# inverse
		'I(1/epi_imputed) ~ np.maximum(bouwjaar, 1900) + I(1/epi_pc6_average) + woningtype'
		'I(1/epi_imputed) ~ np.maximum(bouwjaar, 1900) + epi_inv_pc6_average + woningtype'
		# log
		'np.log(epi_imputed) ~ np.maximum(bouwjaar, 1900) + np.log(epi_pc6_average) + woningtype'
		'np.log(epi_imputed) ~ np.maximum(bouwjaar, 1900) + epi_log_pc6_average + woningtype'
	]
	for formula in formulas:
		result = multiple_linear_regression(df, formula)
		process_regression_result(result, alpha=0.05)

def get_95_interval(df):
	formula = 'np.log(epi_imputed) ~ np.maximum(bouwjaar, 1900) + epi_log_pc6_average + woningtype'
	result = multiple_linear_regression(df, formula)

	alphas = [0.05, 0.04, 0.03, 0.025, 0.02]
	for alpha in alphas:
		process_regression_result(result, alpha=alpha)

def main():
	df = get_energy_labels()
	compare_formulas(df)
	get_95_interval(df)

if __name__ == '__main__':
	main()
