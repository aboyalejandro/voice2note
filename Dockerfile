# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Avoid __pycache__
ENV PYTHONDONTWRITEBYTECODE=1

# Copy the rest of the application code into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run main.py when the container launches
CMD ["python", "main.py"]
