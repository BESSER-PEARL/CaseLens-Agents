# Use the official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Copy the rest of the app
COPY agents agents
COPY app app
COPY run.py .

EXPOSE 8501

ENV PYTHONPATH=/app

# Command to run your app
CMD ["python", "run.py"]
