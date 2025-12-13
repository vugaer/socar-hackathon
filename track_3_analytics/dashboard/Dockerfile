FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY ml_predictor.py .
COPY templates/ templates/
COPY static/ static/
COPY data_marts/ data_marts/

EXPOSE 80

CMD ["python", "app.py"]
