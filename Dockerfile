# BUILD STAGE
FROM ubuntu:latest AS build

# Set the working directory
WORKDIR /djerba

# Install Python 3.10.6 and dependencies for building
RUN apt-get update && \
    apt-get install -y dumb-init software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install system build tools and dependencies for building Python wheels
RUN apt-get update && \
    apt-get install -y build-essential \
                       libssl-dev \
                       libcairo2-dev \
                       libgif-dev \
                       libffi-dev \
                       python3-dev \
                       zlib1g-dev \
                       libjpeg-dev \
                       libpng-dev \
                       libxml2-dev \
                       libxslt1-dev \
                       libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment and activate it
RUN python3.10 -m venv /opt/venv

# Ensure the virtual environment is used for subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip, setuptools, and wheel inside the virtual environment
RUN pip install --upgrade pip setuptools wheel

# Copy the local Djerba files into the container for building
COPY . .

# Copy wkhtmltopdf into the container
COPY wkhtmltopdf .

# install pyyaml==5.4.1; module 'crimson' is incompatible with latest pyyaml
RUN pip install "cython<3.0.0" wheel && pip install pyyaml==5.4.1 --no-build-isolation

# Install Djerba dependencies inside the virtual environment
# --pre flag to circumvent matplotlib error; see https://stackoverflow.com/a/69982317
RUN pip install . -r djerba_requirements.txt --pre

# RUNTIME STAGE
FROM ubuntu:latest AS runtime

# Set the working directory
WORKDIR /djerba

# Install Python 3.10.6 runtime (no dev tools)
RUN apt-get update && \
    apt-get install -y dumb-init software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-venv && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the build stage
COPY --from=build /opt/venv /opt/venv

# Copy the Djerba code from the build stage
COPY --from=build /djerba /djerba

# Ensure the virtual environment is used for subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Set Djerba environment variables
ENV DJERBA_RUN_DIR="/opt/venv/lib/python3.10/site-packages/djerba/data"

# Define the entry point to use Djerba as a CLI tool
ENTRYPOINT ["dumb-init", "--", "python3", "/djerba/src/bin/djerba.py"]
CMD echo "No command specified"
