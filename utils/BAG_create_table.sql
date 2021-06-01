-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS bag
(
identificatie varchar PRIMARY KEY,
geometry varchar,
postcode varchar,
adres varchar,
oppervlakte integer,
bouwjaar integer,
sloopjaar integer,
nr_verdiepingen integer,
pand_aandeel double precision, -- check: how precise is double precision?
woningtype varchar,
pand_id varchar,
buurt_id varchar
);
