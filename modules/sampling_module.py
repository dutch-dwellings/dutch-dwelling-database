import os
import random
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class SamplingModule(BaseModule):

	def process(self, dwelling):
		for name, options in dwelling.sampling_outputs.items():
			distribution_value = dwelling.attributes[options['distribution']]
			dwelling.attributes[name] = self.sample(distribution_value, options['output_type'])

	def sample(self, value, output_type):
		if output_type == 'boolean':
			return self.sample_boolean(value)
		else:
			raise NotImplementedError(f'Have not implemented a sample method for output_type {output_type}')

	def sample_boolean(self, value):
		if type(value) != float:
			raise ValueError(f"Expected type 'float' while sampling for boolean, but got: {type(value)}")
		if (value < 0) or (value > 1):
			raise ValueError(f"Expected value between 0-1 while sampling for boolean, but got: {value}")

		cutoff = random.random()
		if value < cutoff:
			return False
		else:
			return True
