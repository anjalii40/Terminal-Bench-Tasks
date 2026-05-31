FROM python:3.10.14-slim

WORKDIR /app

RUN mkdir -p /app/state /app/input /app/output /app/backup

COPY inventory_manager.py /app/inventory_manager.py
COPY simulate_crash.py /app/simulate_crash.py
COPY initial_state.json /app/initial_state.json
COPY order.json /app/input/order.json
COPY order2.json /app/input/order2.json

RUN pip install pytest==8.3.2 pytest-json-ctrf==0.3.5
