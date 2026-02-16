FROM python:3.11-slim

WORKDIR /app

COPY requirements-observability.txt /app/requirements-observability.txt
RUN pip install --no-cache-dir -r /app/requirements-observability.txt

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY data /app/data
COPY taxonomy /app/taxonomy

RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["uvicorn", "tonesight_ns8.observability_api:app", "--host", "0.0.0.0", "--port", "8080"]
