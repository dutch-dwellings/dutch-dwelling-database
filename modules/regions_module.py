import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule
from classes import PC6, Buurt

class RegionsModule(BaseModule):
	'''
	Adds the different regional spatial levels to
	a dwelling.
	'''

	def __init__(self, connection, **kwargs):
		super().__init__(connection, **kwargs)
		regional_modules = kwargs.get('regional_modules', [])
		self.pc6s = {}
		self.buurten = {}
		self.regional_modules = {
			'pc6': [module for module in regional_modules if 'pc6' in module.supports],
			'buurt': [module for module in regional_modules if 'buurt' in module.supports]
		}
		self.pc6_dwelling_modules = kwargs.get('pc6_dwelling_modules', [])
		self.buurt_dwelling_modules = kwargs.get('buurt_dwelling_modules', [])

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return
		self.add_pc6(dwelling)
		self.add_buurt(dwelling)

	def add_pc6(self, dwelling):
		pc6 = dwelling.attributes['pc6']

		if pc6 in self.pc6s:
			pc6_instance = self.pc6s[pc6]
		else:
			kwargs = {
				'pc6_modules': self.regional_modules['pc6'],
				'pc6_dwelling_modules': self.pc6_dwelling_modules
			}
			pc6_instance = PC6(pc6, self.connection, **kwargs)
			self.pc6s[pc6] = pc6_instance

		dwelling.regions['pc6'] = pc6_instance
		pc6_instance.add_dwelling(dwelling)

	def add_buurt(self, dwelling):
		buurt_id = dwelling.attributes['buurt_id']

		if buurt_id in self.buurten:
			buurt_instance = self.buurten[buurt_id]
		else:
			kwargs = {
				'buurt_modules': self.regional_modules['buurt'],
				'buurt_dwelling_modules': self.buurt_dwelling_modules
			}
			buurt_instance = Buurt(buurt_id, self.connection, **kwargs)
			self.buurten[buurt_id] = buurt_instance

		dwelling.regions['buurt'] = buurt_instance
		buurt_instance.add_dwelling(dwelling)
