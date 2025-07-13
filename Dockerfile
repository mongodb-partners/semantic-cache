FROM python:3.12-slim

# Set up working directory
WORKDIR /code

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

# Copy all application code
COPY ./main.py /code/
COPY ./config.py /code/
COPY ./database/ /code/database/
COPY ./models/ /code/models/
COPY ./monitoring /code/monitoring/
COPY ./services/ /code/services/
COPY ./utils/ /code/utils/


# Alternative: Copy the entire project directory
# COPY . /code/

# Make sure directory permissions are correct
RUN chmod -R 755 /code

# Create logs directory
RUN mkdir -p logs

# Expose the API port
EXPOSE 8183

# Run the FastAPI application
ENTRYPOINT ["python3", "main.py"]