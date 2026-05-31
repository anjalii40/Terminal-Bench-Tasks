FROM python:3.10.14-slim

WORKDIR /

RUN pip install --no-cache-dir pytest==8.3.2

COPY register.py /environment/
COPY sample_job/ /environment/sample_job/
COPY fixtures/ /environment/fixtures/
