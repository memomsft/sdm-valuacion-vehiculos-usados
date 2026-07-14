# Notebook: nb_generar_datos_sdm
# Ejecutar en Fabric Notebook — Runtime: Spark
# Versión: 2.0 — incluye Qashqai, Pathfinder y precios por modelo

import pandas as pd
import random
from datetime import datetime, timedelta

# Semilla para reproducibilidad
random.seed(42)

# Marcas que vende Santo Domingo Motors
MARCAS_SDM = ['Nissan', 'Chevrolet', 'Suzuki', 'Infiniti', 'Cadillac', 'Yamaha']

MODELOS = {
    'Nissan':    ['Sentra', 'Versa', 'X-Trail', 'Frontier', 'Kicks', 'Qashqai', 'Pathfinder'],
    'Chevrolet': ['Tracker', 'Cruze', 'Equinox', 'Trax', 'Silverado', 'Onix'],
    'Suzuki':    ['Swift', 'Vitara', 'Jimny', 'S-Cross', 'Grand Vitara'],
    'Infiniti':  ['Q50', 'QX50', 'Q60', 'QX60', 'QX80'],
    'Cadillac':  ['CT4', 'CT5', 'XT4', 'XT5', 'XT6', 'Escalade'],
    'Yamaha':    ['MT-03', 'YZF-R3', 'FZ-25', 'XMAX 300', 'Tenere 700'],
}

CONDICIONES = ['Excelente', 'Muy Bueno', 'Bueno', 'Regular', 'Deteriorado']

SUCURSALES = [
    'Santo Domingo Central',
    'Santo Domingo Norte',
    'Santiago',
    'Punta Cana',
]

# Factor por condición
FACTOR_CONDICION = {
    'Excelente':   0.90,
    'Muy Bueno':   0.78,
    'Bueno':       0.65,
    'Regular':     0.50,
    'Deteriorado': 0.32,
}

# Precio base por marca (RD$) — refleja precio de mercado usado promedio
PRECIO_BASE_MARCA = {
    'Nissan':    850_000,
    'Chevrolet': 950_000,
    'Suzuki':    650_000,
    'Infiniti':  1_800_000,
    'Cadillac':  3_500_000,
    'Yamaha':    280_000,
}

# Override de precio base por modelo — para modelos premium dentro de una marca
# Alineado con el fallback del app (modelOverrides en PRICING)
PRECIO_BASE_MODELO = {
    'Qashqai':   950_000,   # Nissan Qashqai — SUV compacto premium
    'Pathfinder': 1_800_000, # Nissan Pathfinder — SUV grande
    'Silverado':  2_500_000, # Chevrolet Silverado — pickup premium
}

# Generar tabla de precios de mercado
filas = []
for i in range(1, 201):
    marca = random.choice(MARCAS_SDM)
    modelo = random.choice(MODELOS[marca])
    anio = random.randint(2016, 2023)
    km = random.randint(10_000, 180_000)
    condicion = random.choice(CONDICIONES)
    sucursal = random.choice(SUCURSALES)

    # Usar override de precio si existe para el modelo, sino usar base de marca
    precio_base = PRECIO_BASE_MODELO.get(modelo, PRECIO_BASE_MARCA[marca])

    # Ajuste por año
    factor_anio = 1.0 - (2024 - anio) * 0.07
    # Ajuste por kilómetros
    factor_km = 1.0 - (km / 200_000) * 0.25
    # Ajuste por condición
    factor_cond = FACTOR_CONDICION[condicion]

    precio_mercado = int(precio_base * factor_anio * factor_km * factor_cond)
    precio_compra_sugerido = int(precio_mercado * 0.82)
    dias_inventario = random.randint(5, 95)

    filas.append({
        'id_vehiculo': f'SDM-{str(i).zfill(4)}',
        'marca': marca,
        'modelo': modelo,
        'anio': anio,
        'kilometraje': km,
        'condicion_declarada': condicion,
        'sucursal': sucursal,
        'precio_mercado_rd': precio_mercado,
        'precio_compra_sugerido_rd': precio_compra_sugerido,
        'dias_en_inventario': dias_inventario,
        'fecha_ingreso': (datetime.today() - timedelta(days=dias_inventario)).strftime('%Y-%m-%d'),
    })

df = pd.DataFrame(filas)

# Guardar como tabla Delta en el Lakehouse
spark.createDataFrame(df).write.format('delta').mode('overwrite').saveAsTable('precios_mercado_usados')
print(f'Tabla creada: {len(df)} registros')
print(f'Modelos únicos: {sorted(df.modelo.unique())}')
print(f'Rango de precios de mercado: RD$ {df.precio_mercado_rd.min():,} – RD$ {df.precio_mercado_rd.max():,}')
