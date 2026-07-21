# Use an official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app



# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

# Expose the port the FastAPI app runs on
EXPOSE 8001

# Run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
