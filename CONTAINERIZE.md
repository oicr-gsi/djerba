## Why containerize?

The current barrier to running djerba outside OICR:
- 5 environment variables must be set
- Python ≥ 3.10.6 with 15+ packages
- R with specific packages
- wkhtmltopdf binary
- OncoKB cache pre-populated
- Reference data in the right location

A Docker image bakes all of this in. The user mounts their data and runs one command.

---

## Docker

### Multi-stage build (`Dockerfile`)

```
Stage 1 (builder):
  python:3.11-slim
  → pip install all Python deps
  → produces a clean site-packages dir

Stage 2 (final):
  python:3.11-slim
  → copy site-packages from builder
  → apt-get install: r-base, wkhtmltopdf, build-essential
  → install R packages (ggplot2, dplyr, etc.)
  → copy source code
  → set env vars
  → ENTRYPOINT: djerba.py
```

Multi-stage keeps the final image smaller by not including build tools.

### Usage

```bash
# Build
docker build -t djerba:latest .

# Run a report
docker run --rm \
  -v /path/to/workspace:/workspace \
  -v /path/to/data:/data:ro \
  -v /path/to/reference:/reference:ro \
  -v /path/to/output:/output \
  -e ONCOKB_API_KEY=your_key \
  djerba:latest \
  report \
    -i /data/config.ini \
    -w /workspace \
    -j /output/report.json \
    -o /output \
    -p

# Just render from existing JSON
docker run --rm \
  -v /path/to/output:/output \
  djerba:latest \
  render -j /output/report.json -o /output -p
```

### Environment variables in container

Non-sensitive variables are set as defaults in the Dockerfile:
```dockerfile
ENV DJERBA_BASE_DIR=/djerba
ENV DJERBA_RUN_DIR=/reference
ENV PYTHONPATH=/djerba/src/lib
```

Sensitive variables (OncoKB key, CouchDB credentials) are passed at runtime via `-e` or a `.env` file.

---

## docker-compose 

```yaml
# docker-compose.yml
services:
  djerba:
    build: .
    volumes:
      - ./workspace:/workspace
      - ${DATA_DIR}:/data:ro
      - ${REFERENCE_DIR}:/reference:ro
      - ./output:/output
    env_file: .env
    command: >
      report
        -i /data/config.ini
        -w /workspace
        -j /output/report.json
        -o /output
        -p
```

Create `.env` from `.env.example`:
```bash
cp .env.example .env
nano .env  # fill in ONCOKB_API_KEY, DATA_DIR, REFERENCE_DIR
docker-compose up
```

---