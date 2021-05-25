-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS bag
(
identificatie varchar,
geometry varchar,
postcode varchar,
adres varchar,
oppervlakte int, -- int or double precision? And will Postgres error when converting float to int?
bouwjaar int,
sloopjaar int,
nr_verdiepingen int,
pand_aandeel double precision, -- check: how precise is double precision?
woningtype varchar,
pand_id varchar,
buurt_id varchar
);
