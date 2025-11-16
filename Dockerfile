# Use official slim Python image
FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# copy requirements then install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy application
COPY . /app

EXPOSE 8000

# run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
