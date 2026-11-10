-- Seeds dw.dim_product: 14 styles x 2 colours x sizes (XS-XL, or ONE for accessories) = 124 SKUs.
-- No-op when the table already has rows.
WITH styles (style_code, style_name, department, category, list_price, unit_cost,
             color1, code1, color2, code2, sized) AS (
    VALUES
        ('W-JKT-001', 'Kurtka pikowana damska', 'WOMEN',  'Kurtki',    399.00, 148.00, 'Czarny',    'CZA', 'Piaskowy',  'PIA', true),
        ('W-JKT-002', 'Parka damska',           'WOMEN',  'Kurtki',    499.00, 189.00, 'Khaki',     'KHA', 'Czarny',    'CZA', true),
        ('W-DRS-001', 'Sukienka midi',          'WOMEN',  'Sukienki',  199.00,  62.00, 'Czarny',    'CZA', 'Bordowy',   'BOR', true),
        ('W-DRS-002', 'Sukienka koszulowa',     'WOMEN',  'Sukienki',  179.00,  55.00, 'Granatowy', 'GRA', 'Ecru',      'ECR', true),
        ('W-KNT-001', 'Sweter oversize',        'WOMEN',  'Swetry',    159.00,  48.00, 'Szary',     'SZA', 'Kremowy',   'KRE', true),
        ('W-JNS-003', 'Jeansy skinny',          'WOMEN',  'Jeansy',    169.00,  52.00, 'Niebieski', 'NIE', 'Czarny',    'CZA', true),
        ('W-TSH-001', 'T-shirt basic damski',   'WOMEN',  'T-shirty',   59.00,  14.00, 'Ecru',      'ECR', 'Czarny',    'CZA', true),
        ('M-JKT-001', 'Kurtka miejska',         'MEN',    'Kurtki',    429.00, 160.00, 'Czarny',    'CZA', 'Granatowy', 'GRA', true),
        ('M-KNT-001', 'Sweter z dzianiny',      'MEN',    'Swetry',    179.00,  54.00, 'Granatowy', 'GRA', 'Szary',     'SZA', true),
        ('M-JNS-001', 'Jeansy regular',         'MEN',    'Jeansy',    189.00,  58.00, 'Niebieski', 'NIE', 'Grafitowy', 'GRF', true),
        ('M-TSH-001', 'T-shirt basic',          'MEN',    'T-shirty',   59.00,  14.00, 'Ecru',      'ECR', 'Czarny',    'CZA', true),
        ('M-SHI-001', 'Koszula oxford',         'MEN',    'Koszule',   199.00,  60.00, 'Ecru',      'ECR', 'Lazurowy',  'LAZ', true),
        ('A-BAG-001', 'Torebka shopper',        'WOMEN',  'Akcesoria', 249.00,  78.00, 'Czarny',    'CZA', 'Koniakowy', 'KON', false),
        ('A-SCF-001', 'Szalik zimowy',          'UNISEX', 'Akcesoria',  89.00,  26.00, 'Szary',     'SZA', 'Bordowy',   'BOR', false)
),
sizes (size, sized) AS (
    VALUES ('XS', true), ('S', true), ('M', true), ('L', true), ('XL', true), ('ONE', false)
)
INSERT INTO dw.dim_product
    (sku, style_code, style_name, department, category, color, size, list_price, unit_cost, is_active)
SELECT  s.style_code || '-' || c.code || '-' || z.size,
        s.style_code,
        s.style_name,
        s.department,
        s.category,
        c.color,
        z.size,
        s.list_price,
        s.unit_cost,
        true
FROM    styles AS s
CROSS JOIN LATERAL (VALUES (s.color1, s.code1), (s.color2, s.code2)) AS c (color, code)
JOIN    sizes AS z ON z.sized = s.sized
WHERE   NOT EXISTS (SELECT 1 FROM dw.dim_product)
ORDER BY s.style_code COLLATE "C", c.code COLLATE "C", z.size COLLATE "C";
