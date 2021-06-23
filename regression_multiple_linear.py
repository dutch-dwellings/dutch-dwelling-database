import numpy as np
from scipy import stats
from sklearn import linear_model
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.predstd import wls_prediction_std

from utils.database_utils import get_connection

def soapsuds():
	print('### soap suds ###')
	# https://online.stat.psu.edu/stat501/lesson/5/5.4
	# https://online.stat.psu.edu/onlinecourses/sites/stat501/files/data/soapsuds.txt
	data = [
		# soap, suds
		(4.0, 33),
		(4.5, 42),
		(5.0, 45),
		(5.5, 51),
		(6.0, 53),
		(6.5, 61),
		(7.0, 62)
	]
	x = [[1, val[0]] for val in data]
	y = [val[1] for val in data]
	x_h = [1, 6.2]
	return x, y, x_h

def pastry():
	print('### pastry ###')
	# https://online.stat.psu.edu/onlinecourses/sites/stat501/files/data/pastry.txt
	data = [
		# Rating, Moisture, Sweetness
		(64, 4, 2),
		(73, 4, 4),
		(61, 4, 2),
		(76, 4, 4),
		(72, 6, 2),
		(80, 6, 4),
		(71, 6, 2),
		(83, 6, 4),
		(83, 8, 2),
		(89, 8, 4),
		(86, 8, 2),
		(93, 8, 4),
		(88, 10, 2),
		(95, 10, 4),
		(94, 10, 2),
		(100, 10, 4)
	]
	x = [[1, val[1], val[2]] for val in data]
	y = [val[0] for val in data]
	x_h = [1, 5, 3]
	return x, y, x_h

def bodyfat():
	print('### body fat ###')
	# https://online.stat.psu.edu/onlinecourses/sites/stat501/files/data/bodyfat.txt
	data = [
		# Triceps, Thigh, Midarm, Bodyfat
		(19.5, 43.1, 29.1, 11.9),
		(24.7, 49.8, 28.2, 22.8),
		(30.7, 51.9, 37, 18.7),
		(29.8, 54.3, 31.1, 20.1),
		(19.1, 42.2, 30.9, 12.9),
		(25.6, 53.9, 23.7, 21.7),
		(31.4, 58.5, 27.6, 27.1),
		(27.9, 52.1, 30.6, 25.4),
		(22.1, 49.9, 23.2, 21.3),
		(25.5, 53.5, 24.8, 19.3),
		(31.1, 56.6, 30, 25.4),
		(30.4, 56.7, 28.3, 27.2),
		(18.7, 46.5, 23, 11.7),
		(19.7, 44.2, 28.6, 17.8),
		(14.6, 42.7, 21.3, 12.8),
		(29.5, 54.4, 30.1, 23.9),
		(27.7, 55.3, 25.7, 22.6),
		(30.2, 58.6, 24.6, 25.4),
		(22.7, 48.2, 27.1, 14.8),
		(25.2, 51, 27.5, 21.1)
	]
	x = [[1, val[0], val[1], val[2]] for val in data]
	y = [val[3] for val in data]
	x_h = [1, 21.0, 52.0, 29.5]
	return x, y, x_h

def iqsize():
	print('### IQ size ###')
	# https://online.stat.psu.edu/stat501/lesson/7/7.1
	# https://online.stat.psu.edu/onlinecourses/sites/stat501/files/data/iqsize.txt
	data = [
		# PIQ, Brain, Height, Weight
		(124, 81.69, 64.5, 118),
		(150, 103.84, 73.3, 143),
		(128, 96.54, 68.8, 172),
		(134, 95.15, 65.0, 147),
		(110, 92.88, 69.0, 146),
		(131, 99.13, 64.5, 138),
		(98, 85.43, 66.0, 175),
		(84, 90.49, 66.3, 134),
		(147, 95.55, 68.8, 172),
		(124, 83.39, 64.5, 118),
		(128, 107.95, 70.0, 151),
		(124, 92.41, 69.0, 155),
		(147, 85.65, 70.5, 155),
		(90, 87.89, 66.0, 146),
		(96, 86.54, 68.0, 135),
		(120, 85.22, 68.5, 127),
		(102, 94.51, 73.5, 178),
		(84, 80.80, 66.3, 136),
		(86, 88.91, 70.0, 180),
		(84, 90.59, 76.5, 186),
		(134, 79.06, 62.0, 122),
		(128, 95.50, 68.0, 132),
		(102, 83.18, 63.0, 114),
		(131, 93.55, 72.0, 171),
		(84, 79.86, 68.0, 140),
		(110, 106.25, 77.0, 187),
		(72, 79.35, 63.0, 106),
		(124, 86.67, 66.5, 159),
		(132, 85.78, 62.5, 127),
		(137, 94.96, 67.0, 191),
		(110, 99.79, 75.5, 192),
		(86, 88.00, 69.0, 181),
		(81, 83.43, 66.5, 143),
		(128, 94.81, 66.5, 153),
		(124, 94.94, 70.5, 144),
		(94, 89.40, 64.5, 139),
		(74, 93.00, 74.0, 148),
		(89, 93.59, 75.5, 179)
	]
	x = [[1, val[1], val[2]] for val in data]
	y = [val[0] for val in data]
	x_h = [1, 90, 70]
	return x, y, x_h


def get_labels():
	print('Getting results...')
	connection = get_connection()
	cursor = connection.cursor()
	query = '''
	SELECT
		epi_imputed,
		bag.bouwjaar,
		q.epi_pc6_average,
		CASE
			WHEN bag.woningtype = 'tussenwoning'
			THEN 1
			ELSE 0
		END as tussenwoning,
		CASE
			WHEN bag.woningtype = 'hoekwoning'
			THEN 1
			ELSE 0
		END as hoekwoning,
		CASE
			WHEN bag.woningtype = 'meergezinspand_hoog'
			THEN 1
			ELSE 0
		END as meergezinspand_hoog,
		CASE
			WHEN bag.woningtype = 'meergezinspand_laag_midden'
			THEN 1
			ELSE 0
		END as meergezinspand_laag_midden,
		CASE
			WHEN bag.woningtype = 'twee_onder_1_kap'
			THEN 1
			ELSE 0
		END as twee_onder_1_kap,
		CASE
			WHEN bag.woningtype = 'vrijstaand'
			THEN 1
			ELSE 0
		END as vrijstaand
	FROM
		energy_labels,
		bag,
		(SELECT pc6, AVG(epi_imputed) as epi_pc6_average FROM energy_labels GROUP BY pc6) q
	WHERE
		energy_labels.vbo_id = bag.vbo_id
		AND energieklasse IS NOT NULL
		AND q.pc6 = bag.pc6
	'''
	cursor.execute(query)
	return cursor.fetchall()

def labels():
	print('### energy labels ###')
	results = get_labels()

	print('Converting to dataframe...')
	df = pd.DataFrame(results, columns=['epi_imputed', 'bouwjaar', 'epi_pc6_average', 'tussenwoning', 'hoekwoning', 'meergezinspand_hoog', 'meergezinspand_laag_midden', 'twee_onder_1_kap', 'vrijstaand'])
	y = df['epi_imputed']
	x = df.drop(['epi_imputed'], axis=1)
	x.insert(0, 'constant', 1)

	# building from 2020
	# pc6_average = 1.5
	# type = 'tussenwoning'
	x_h = [1, 2020, 1.5, 1, 0, 0, 0, 0, 0]

	return x, y, x_h, df

def manual_statistics_multiple(x, y, x_h):

	print("\n=== manual ===")

	x = np.array(x)
	print(f'x.dtype: {x.dtype}')
	y = np.array(y)

	n = len(x)
	p = len(x[0])

	x_means = np.mean(x, axis=0)
	y_mean = np.mean(y)
	print('--- descriptive statistics ---')
	print(f'x_means: {x_means}')
	print(f'y_mean: {y_mean}')

	# Least squares estimates in matrix notation
	# b = (X^t X)^-1 X^t Y

	x_t = np.transpose(x)
	print(f'x_t.dtype: {x_t.dtype}')

	print(f'np.dot(x_t, x):\n{np.dot(x_t, x)}')

	x_t_x_inv = np.linalg.inv(np.dot(x_t, x))
	print(f'x_t_x_inv.dtype: {x_t_x_inv.dtype}')
	b = np.dot(np.dot(x_t_x_inv, x_t), y)
	print('\n--- linear regression coefficients ---')
	print(f'x_t_x_inv:\n{x_t_x_inv}')
	print(f'b: {b}')

	y_h_hat = np.dot(b, x_h)

	print('\n--- prediction ---')
	print(f'x_h: {x_h}')
	print(f'y_h_hat: {y_h_hat}')

	y_hat = [np.dot(b, x[i]) for i in range(n)]
	MSE = sum([(y_hat[i] - y[i])**2 for i in range(n)]) / (n - p)
	print(f'MSE: {MSE}')

	var_covar_matrix = MSE * x_t_x_inv
	print(f'var_covar_matrix:\n{var_covar_matrix}\n')

	se_2 = np.diag(var_covar_matrix)
	se = np.sqrt(se_2)
	print(f'se^2: {se_2}')
	print(f'se: {se}\n')

	# https://online.stat.psu.edu/stat501/lesson/7/7.1
	# (beautiful variable names! ...)
	x_h_t_x_t_x_inv_x_h = np.dot(np.dot(np.transpose(x_h), x_t_x_inv), x_h)
	se_y_h = np.sqrt(MSE * x_h_t_x_t_x_inv_x_h)

	alpha = 0.05

	t_multiplier = stats.t.ppf(1 - alpha/2, n-p)

	CI_range_min = y_h_hat - t_multiplier * se_y_h
	CI_range_max = y_h_hat + t_multiplier * se_y_h
	CI_range = (CI_range_min, CI_range_max)
	print(f'CI_range: {CI_range}')

	PI_range_min = y_h_hat - t_multiplier * np.sqrt(MSE + se_y_h**2)
	PI_range_max = y_h_hat + t_multiplier * np.sqrt(MSE + se_y_h**2)
	PI_range = (PI_range_min, PI_range_max)
	print(f'PI_range: {PI_range}')

	return list(b)

def automatic_statistics_multiple(x, y, x_h):
	print("\n\n=== automatic ===")
	clf = linear_model.LinearRegression()
	clf.fit(x, y)

	b = [clf.intercept_, *clf.coef_[1:]]
	print(f'b: {b}')
	print(f'y_h_hat: {clf.predict([x_h])[0]}')

	return b

def automatic_statistics_statsmodel(x, y, x_h):
	print("\n\n=== automatic (statsmodel / dataframe) ===")
	# formula = 'epi_imputed ~ bouwjaar + epi_pc6_average + tussenwoning + hoekwoning + meergezinspand_hoog + meergezinspand_laag_midden + twee_onder_1_kap + vrijstaand'
	# result = smf.ols(formula=formula, data=df).fit()
	result = sm.OLS(y, x).fit()
	print(result.params)
	print(result.summary())

	print(result.cov_type)
	print(dir(result))
	print(f'mse_resid: {result.mse_resid}')
	MSE = result.mse_resid
	print(f'mse_model: {result.mse_model}')
	print(f'mse_total: {result.mse_total}')


	# Adapted from https://stackoverflow.com/a/47191929/7770056.
	alpha = 0.05
	prediction = result.get_prediction(x_h)
	y_h_hat = prediction.predicted_mean[0]
	print(f'y_h_hat: {y_h_hat}')

	var_covar_matrix = result.cov_params()

	se_2 = np.diag(var_covar_matrix)
	se = np.sqrt(se_2)
	print(f'se^2: {se_2}')
	print(f'se: {se}')

	# https://github.com/statsmodels/statsmodels/blob/main/statsmodels/regression/_prediction.py#L187
	var_pred_mean = np.dot(x_h, np.dot(var_covar_matrix, x_h).T)
	print(f'var_pred_mean: {var_pred_mean}')
	n = len(x)
	p = len(x[0])
	t_multiplier = stats.t.ppf(1 - alpha/2, n-p)
	print(f't_multiplier: {t_multiplier}')

	# var_resid = result.var_resid
	se_obs = np.sqrt(MSE + var_pred_mean)
	print(se_obs)

	# https://github.com/statsmodels/statsmodels/blob/main/statsmodels/regression/_prediction.py#L57
	# se_obs = np.sqrt(var_pred_mean + var_resid)


	frame = prediction.summary_frame(alpha=alpha)
	print(frame)


	PI_range_max = float(frame.obs_ci_upper)
	PI_range_min = float(frame.obs_ci_lower)
	PI_range = (PI_range_min, PI_range_max)
	print(f'PI_range: {PI_range}')

	return list(result.params)

def main():

	# x, y, x_h = soapsuds()
	# x, y, x_h = pastry()
	# x, y, x_h = bodyfat()
	x, y, x_h = iqsize()
	# x, y, x_h, df = labels()

	print('Applying manual statistics')
	b_manual = manual_statistics_multiple(x, y, x_h)
	b_automatic = automatic_statistics_multiple(x, y, x_h)
	b_statistics = automatic_statistics_statsmodel(x, y, x_h)

	print("\n\n=== Coefficients ===")
	print(f'b_manual:     {b_manual}')
	print(f'b_automatic:  {b_automatic}')
	print(f'b_statistics: {b_statistics}')

main()
