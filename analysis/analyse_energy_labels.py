from analysis_utils import query_to_table

building_type_query = "SELECT pand_gebouwtype, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_gebouwtype"
building_type_desc = "Number of dwellings per building type (EP-Online)"

energy_label_query = "SELECT pand_energieklasse, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_energieklasse"
energy_label_desc = "Number of dwellings per energy label (EP-Online)"

query_to_table(building_type_query, title=building_type_desc, total=True)
query_to_table(energy_label_query, title=energy_label_desc, total=True)


# TODO:
# check internal correlation in a pand with multiple verblijfsobjecten.
# Helpful concept:
# Intraclass correlation: https://en.wikipedia.org/wiki/Intraclass_correlation
# In thise case, the buildings (panden) are the groups, and we see energy labels
# from dwellings inside that building as a measurement.
#
# To get these panden with multiple energy labels:
# SELECT pand_bagpandid FROM energy_labels GROUP BY pand_bagpandid HAVING COUNT(*) > 1
# And to select the labels in those panden:
# SELECT pand_bagpandid, pand_energieklasse FROM energy_labels WHERE pand_bagpandid IN (SELECT pand_bagpandid FROM energy_labels GROUP BY pand_bagpandid HAVING COUNT(*) > 1) AND pand_gebouwklasse = 'W';
#
# Final use case:
# Predict an energy_label (or a 95% range of energy_labels) based on other measured energy_labels
# in the same building.
#
# Related: doing this not for dwellings in the same building, but dwellings neighbouring each other, or within a certain radius of each other, or within the same block.
