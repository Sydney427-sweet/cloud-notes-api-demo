# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port (Render expects 10000+ or default 5000)
EXPOSE 5000

# Run the app with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
