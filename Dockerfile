<<<<<<< HEAD
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT app:app
=======
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 5000

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]
>>>>>>> 5eb45e9 (Initial commit - CLoud Notes API complete)
