FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEMORY_PYTHON_PORT=8092 \
    MEMORY_PYTHON_HOST=0.0.0.0

COPY python-agent/requirements.txt /app/python-agent/requirements.txt
RUN pip install --no-cache-dir -r /app/python-agent/requirements.txt
COPY python-agent /app/python-agent

EXPOSE 8092
CMD ["python", "/app/python-agent/app.py"]
