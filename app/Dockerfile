FROM python:3.10-slim
# Install curl and dnsutils (for nslookup)
RUN apt-get update && \
    apt-get install -y curl dnsutils && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV PYTHONPATH=/app
ENV AWS_DEFAULT_REGION=us-west-2
CMD ["streamlit", "run", "src/ui/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
