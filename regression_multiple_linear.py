import numpy as np
from scipy import stats
from sklearn import linear_model

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

def manual_statistics_multiple(x, y):

	print("=== manual ===")

	x = np.array(x)
	y = np.array(y)

	n = len(x)
	p = len(x[0])

	x_means = np.mean(x, axis=0)
	y_mean = np.mean(y)
	print(f'x_means: {x_means}')
	print(f'y_mean: {y_mean}')

	# Least squares estimates in matrix notation
	# b = (X^t X)^-1 X^t Y

	x_t = np.transpose(x)

	x_t_x_inv = np.linalg.inv(np.dot(x_t, x))

	b = np.dot(np.dot(x_t_x_inv, x_t), y)
	print(f'b: {b}')

	y_h_hat = np.dot(b, x_h)

	print(f'x_h: {x_h}')
	print(f'y_h_hat: {y_h_hat}')

	y_hat = [np.dot(b, x[i]) for i in range(n)]
	MSE = sum([(y_hat[i] - y[i])**2 for i in range(n)]) / (n-p)
	print(f'MSE: {MSE}')

	var_covar_matrix = MSE * x_t_x_inv
	print(f'var_covar_matrix: {var_covar_matrix}')

	se_2 = np.diag(var_covar_matrix)
	se = np.sqrt(se_2)
	print(f'se^2: {se_2}')
	print(f'se: {se}')

	cov_b1_b2 = var_covar_matrix[1][2]
	corr_b1_b2 = cov_b1_b2 / (se[1] * se[2])
	print(f'cov_b1_b2: {cov_b1_b2}')
	print(f'corr_b1_b2: {corr_b1_b2}')

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

	print(x_t_x_inv)

def automatic_statistics_multiple(x, y):
	print("\n=== automatic ===")
	clf = linear_model.LinearRegression()
	clf.fit(x, y)
	print(clf.intercept_)
	print(clf.coef_)
	print(clf.rank_)
	print(clf.singular_)
	print(clf.predict([x_h]))

def main():
	manual_statistics_multiple(x, y)
	automatic_statistics_multiple(x, y)

main()
