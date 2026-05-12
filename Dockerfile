# Use a standard Ubuntu base for better support of bioinformatics tools (R, etc.)
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.10, R, and other essential tools
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    r-base \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libcairo2-dev \
    libxt-dev \
    git \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as the default python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# Install R dependencies
RUN R -e "install.packages(c('optparse', 'dplyr', 'ggplot2', 'scales', 'cowplot'), repos='https://cloud.r-project.org/')"

# Create app directory
WORKDIR /app

# Copy the source code
COPY . /app

# Install Python dependencies
# setup.py now includes gcsfs and google-cloud-storage
RUN pip3 install --no-cache-dir .

# Set environment variables with defaults (using the ones we refactored)
# These can be overridden at runtime via docker run -e or K8s env spec
ENV WHIZBAM_PATTERN_ROOT="/.mounts/labs/prod/whizbam"
ENV TCGA_DATA_PATH="/.mounts/labs/CGI/gsi/tools/RODiC/data"
ENV GEP_REFERENCE_PATH="/.mounts/labs/CGI/gsi/tools/djerba/gep_reference.txt.gz"
ENV ONCOKB_CACHE_PATH="/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch"

# Define the default command
# djerba.py is installed into the path by setup.py
ENTRYPOINT ["djerba.py"]
CMD ["--help"]
