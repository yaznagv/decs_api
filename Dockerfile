########### BASE STAGE ###########
FROM python:3.10.8-alpine AS base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy base requirements
COPY ./requirements.txt /app/

# install base dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    && apk add --no-cache py3-lxml mariadb-dev \
    && pip install --upgrade pip setuptools && pip install --no-cache-dir -r /app/requirements.txt \
    && apk del .build-deps

EXPOSE 8000

WORKDIR /app


########### DEV STAGE ###########
FROM base AS dev



########### PRODUCTION STAGE ###########
FROM base AS prod

# create a app user
RUN addgroup -S appuser && adduser -S appuser -G appuser

# create directory for collectstatic command
RUN mkdir /app/static_files

# copy project
COPY --chown=appuser:appuser . /app/

# change to the app user
USER appuser