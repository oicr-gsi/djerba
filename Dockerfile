# Djerba — multi-stage Docker build
#
# Stage 1: builder: installs Python dependencies into a clean prefix
# Stage 2: final: adds R, wkhtmltopdf, and copies the built package
#
# Usage:
#   docker build -t djerba:latest .
#   docker run --rm \
#     -v /path/to/workspace:/workspace \
#     -v /path/to/data:/data:ro \
#     -v /path/to/reference:/reference:ro \
#     -v /path/to/output:/output \
#     -e ONCOKB_API_KEY=your_key \
#     djerba:latest \
#     report -i /data/config.ini -w /workspace -j /output/report.json -o /output -p

# Stage 1: builder
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build tools needed by some Python packages (e.g pycairo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only what pip needs to install
COPY setup.py README.md ./
COPY src/lib/ src/lib/
COPY src/bin/ src/bin/

# Install into a prefix directory so we can copy it cleanly
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: final 
FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/oicr-gsi/djerba"
LABEL org.opencontainers.image.description="Djerba clinical genomics report generator"
LABEL org.opencontainers.image.licenses="GPL-3.0"

WORKDIR /djerba

# Install system dependencies:
#   r-base + r-cran-* — R and packages used by plugins
#   wkhtmltopdf       — HTML → PDF conversion
#   libcairo2         — pycairo runtime
#   fonts-*           — font support for wkhtmltopdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-cran-ggplot2 \
    r-cran-dplyr \
    r-cran-tidyr \
    r-cran-gridextra \
    r-cran-reshape2 \
    r-cran-ggrepel \
    r-cran-cowplot \
    r-cran-broom \
    r-cran-car \
    r-cran-rstatix \
    wkhtmltopdf \
    libcairo2 \
    fonts-liberation \
    fonts-dejavu-core \
    xfonts-base \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install R packages only available from CRAN (not in Debian apt)
RUN Rscript -e "install.packages('ggpubr', repos='https://cloud.r-project.org/')"

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy source 
COPY src/ src/

# Non-sensitive environment defaults, override at runtime for sensitive values
ENV DJERBA_BASE_DIR=/djerba
ENV DJERBA_RUN_DIR=/reference
ENV PYTHONPATH=/djerba/src/lib
ENV PATH=/djerba/src/bin:$PATH

# Mount points
VOLUME ["/workspace", "/data", "/reference", "/output"]

# wkhtmltopdf needs a display for some PDF rendering, using Xvfb as virtual display
ENV DISPLAY=:99
RUN printf '#!/bin/sh\nXvfb :99 -screen 0 1024x768x24 &\nexec "$@"\n' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh", "djerba.py"]
CMD ["--help"]
