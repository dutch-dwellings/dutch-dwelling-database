from database_utils import get_cursor

cur = get_cursor()
cur.execute("SELECT pand_energieklasse, pand_projectnaam FROM energy_labels WHERE pand_gebouwklasse = 'U'")
records = cur.fetchall()
print(records)
