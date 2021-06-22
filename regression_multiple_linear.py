import numpy as np

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

x = [[1, val[1], val[2], val[3]] for val in data]
x = np.array(x)
y = [val[0] for val in data]
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

b = np.dot(np.dot(np.linalg.inv(np.dot(x_t, x)), x_t), y)
print(f'b: {b}')

x_h = x[0]
y_h_hat = np.dot(b, x_h)
y_h = y[0]

print(f'x_h: {x_h}')
print(f'y_h_hat: {y_h_hat}')
print(f'y_h: {y_h}')

y_hat = [np.dot(b, x[i]) for i in range(n)]
print([(y[i] - y_hat[i])**2 for i in range(n)])
