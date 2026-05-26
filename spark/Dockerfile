FROM bitnami/spark:3.5.0

# Set working directory
WORKDIR /opt/spark

# Install system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy configurations
COPY configs/ /opt/spark/configs/

# Expose ports
EXPOSE 7077 8080 4040

# Switch to spark user
USER 1001

CMD ["bin/spark-class", "org.apache.spark.deploy.master.Master"]
