# "Access to Work | Île-de-France": Dash app (FastAPI backend) serving the precomputed results.
#
# Build and run from the repository root:
#   docker build -f deploy/Dockerfile -t access-to-work .
#   docker run -d --name access-to-work --restart unless-stopped -p 127.0.0.1:8050:8000 access-to-work
#
# The image holds the app and data/processed/ only (about 18 MB of results). The routing pipeline,
# r5py and Java are not shipped: the app never computes travel times.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY deploy/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY utils/ /srv/utils/
COPY pipeline/__init__.py pipeline/config.py /srv/pipeline/
COPY app/ /srv/app/
COPY data/processed/ /srv/data/processed/

# Run as an unprivileged user.
RUN useradd --system --no-create-home app && chown -R app /srv
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')" || exit 1

# One worker uses about 520 MB of memory once every view has been opened (measured locally), so
# plan for a server with at least 1 GB. Add "--workers", "2" only with 2 GB or more.
CMD ["uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
