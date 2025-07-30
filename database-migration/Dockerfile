FROM python:3-slim AS builder
ADD . /app
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app packaging

FROM python:3-slim
# Install git to run tasks
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

COPY --from=builder /app /app

WORKDIR /app
ENV PYTHONPATH=/app
CMD ["python", "/app/main.py"]
