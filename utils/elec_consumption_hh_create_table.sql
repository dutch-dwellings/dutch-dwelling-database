-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS elec_consumption_households
(
house_type varchar,
consumption_per_household int,
consumption_per_m2 int
);
