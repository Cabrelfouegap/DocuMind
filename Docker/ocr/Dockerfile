FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY ocr/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ocr/ .
EXPOSE 8002
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8002"]
