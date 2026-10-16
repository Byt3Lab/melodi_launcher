FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system melodi \
    && useradd --system --gid melodi --home-dir /home/melodi --create-home melodi \
    && mkdir -p /app/config /app/logs \
    && chown -R melodi:melodi /app /home/melodi

COPY --chown=melodi:melodi app/ ./app/
COPY --chown=melodi:melodi templates/ ./templates/
COPY --chown=melodi:melodi static/ ./static/
COPY --chown=melodi:melodi run.py .

USER melodi

EXPOSE 8080

CMD ["python", "run.py"]
