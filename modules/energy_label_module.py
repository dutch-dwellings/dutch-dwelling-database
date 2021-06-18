import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule, BaseRegionalModule

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
		super().process(dwelling)
		vbo_id = dwelling.attributes['vbo_id']
		energy_label = self.get_energy_label(vbo_id)
		dwelling.attributes['energy_label'] = energy_label

class EnergyLabelRegionalModule(BaseRegionalModule):

	def process_pc6(self, pc6):
		pass

	supports = ['pc6']
