FROM apache/airflow:2.9.1-python3.11
USER root
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir \
    pymongo==4.7.2 \
    requests==2.32.2 \
    python-dotenv==1.0.1 \
    easyocr \
    PyMuPDF \
    Pillow \
    numpy \
    spacy
RUN python -m spacy download fr_core_news_md