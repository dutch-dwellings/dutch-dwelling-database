import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule
from classes import PC6

class RegionsModule(BaseModule):
	'''
	Adds the different regional spatial levels to
	a dwelling.
	'''

	def __init__(self, connection, regional_modules):
		super().__init__(connection)
		self.pc6s = {}
		self.regional_modules = {
			'pc6': [module for module in regional_modules if 'pc6' in module.supports]
		}

	def process(self, dwelling):
		self.add_pc6(dwelling)

	def add_pc6(self, dwelling):
		pc6 = dwelling.attributes['pc6']

		if pc6 in self.pc6s:
			pc6_instance = self.pc6s[pc6]
		else:
			pc6_modules = self.regional_modules['pc6']
			pc6_instance = PC6(pc6, pc6_modules)
			self.pc6s[pc6] = pc6_instance

		dwelling.attributes['pc6'] = pc6_instance
