# Step 1: Use an official Python image as the base image
FROM python:3.9-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the local code to the container
COPY .. /app

# Step 4: Install the Python dependencies
# First, we copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Expose the port that the app will run on (FastAPI uses 8000 by default)
EXPOSE 8000

# Step 6: Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "project2:api", "--host", "0.0.0.0", "--port", "8000"]
