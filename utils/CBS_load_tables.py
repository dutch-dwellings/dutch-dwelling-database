from CBS_utils import load_cbs_table

def main():

	# Energieverbruik particuliere woningen; woningtype, wijken en buurten, 2018
	# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=84585NED&_theme=279
	load_cbs_table("84585NED")

	# Woningen; hoofdverwarmings; buurt 2019
	# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=84983NED&_theme=126
	load_cbs_table("84983NED")

	# add any other tables as you please...
	# load_cbs_table(table_id)

if __name__ == "__main__":
	main()
