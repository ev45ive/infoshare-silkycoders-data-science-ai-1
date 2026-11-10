# Obraz Airflow z zależnościami BC-01. libgomp1 jest wymagane przez LightGBM (OpenMP).
FROM apache/airflow:3.4.0

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir holidays==0.108 python-dateutil lightgbm==4.7.0
