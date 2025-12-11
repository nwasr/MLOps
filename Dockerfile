# Use a lightweight Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only requirements first for layer caching
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and model directory (model artifact should be present at build time)
COPY app.py .
COPY templates/ templates/
COPY model/ model/

EXPOSE 5000

CMD ["python", "app.py"]
