-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS bag
(
	vbo_id character(16) PRIMARY KEY,
	geometry varchar,
	pc6 character(6),
	adres varchar,
	oppervlakte integer,
	bouwjaar integer,
	sloopjaar integer,
	nr_verdiepingen integer,
	pand_aandeel double precision, -- check: how precise is double precision?
	woningtype varchar,
	pand_id character(16),
	buurt_id character(16)
);
