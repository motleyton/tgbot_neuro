FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --system targetbot \
    && adduser --system --ingroup targetbot targetbot

# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt requirements.txt
# Upgrade pip and install pip-tools
RUN pip install -U pip
RUN pip install -U pip-tools
# Install dependencies
RUN pip-sync requirements.txt && rm -rf requirements.txt

WORKDIR /app
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
RUN chown targetbot /docker-entrypoint.sh
COPY ./service_account_file.json service_account_file.json
COPY ./translations.json translations.json
COPY --chown=targetbot:targetbot ./bot /app

USER targetbot

CMD ["python", "main.py"]
