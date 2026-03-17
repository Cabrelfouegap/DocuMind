FROM apache/airflow:2.9.1-python3.11
USER root
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir pymongo==4.7.2 requests==2.32.2 python-dotenv==1.0.1
