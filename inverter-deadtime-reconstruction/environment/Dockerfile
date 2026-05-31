FROM python:3.11.9-slim-bookworm

WORKDIR /

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++-12 \
    && ln -s /usr/bin/g++-12 /usr/local/bin/g++ \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pytest==8.3.2

COPY inverter.cpp /environment/inverter.cpp
COPY sample_job/ /environment/sample_job/
