-- Seeds dw.dim_store: five physical stores and the online shop. No-op when the table already has rows.
INSERT INTO dw.dim_store
    (store_code, store_name, city, region, channel, format, sales_area_m2, opened_date, remodel_date)
SELECT  v.*
FROM (
    VALUES
        ('S-WAW-01', 'Warszawa Arkadia',    'Warszawa', 'Mazowieckie',   'STORE',  'Galeria',    420,  date '2016-04-15', NULL::date),
        ('S-WAW-02', 'Warszawa Mokotow',    'Warszawa', 'Mazowieckie',   'STORE',  'Galeria',    260,  date '2019-09-01', NULL),
        ('S-KRK-01', 'Krakow Rynek',        'Krakow',   'Malopolskie',   'STORE',  'Ulica',      320,  date '2017-11-20', date '2026-04-01'),
        ('S-POZ-01', 'Poznan Stary Browar', 'Poznan',   'Wielkopolskie', 'STORE',  'Galeria',    300,  date '2018-03-10', NULL),
        ('S-GDA-01', 'Gdansk Forum',        'Gdansk',   'Pomorskie',     'STORE',  'Galeria',    240,  date '2021-10-05', NULL),
        ('S-ONL-01', 'Sklep internetowy',   '-',        'Online',        'ONLINE', 'E-commerce', NULL, date '2015-01-01', NULL)
) AS v (store_code, store_name, city, region, channel, format, sales_area_m2, opened_date, remodel_date)
WHERE NOT EXISTS (SELECT 1 FROM dw.dim_store);
