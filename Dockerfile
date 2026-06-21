FROM python:3.12-slim

WORKDIR /app

# Install system deps + Node.js for Code Runner + Git + Flyctl
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install flyctl
RUN curl -L https://fly.io/install.sh | sh
ENV PATH="/root/.fly/bin:${PATH}"

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

# Create workspace with write permissions
RUN mkdir -p /app/workspace && chmod -R 777 /app/workspace

# Git init for self-modification
RUN git init && \
    git config --global user.email "rabie@auto-makah.sa" && \
    git config --global user.name "Rabie" && \
    git add -A && git commit -m "auto-makah-agent-os-init" || true

EXPOSE 8000

# Start script: configure flyctl auth from secret, then run app
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'if [ -n "$FLY_API_TOKEN" ]; then' >> /start.sh && \
    echo '  export FLY_ACCESS_TOKEN="$FLY_API_TOKEN"' >> /start.sh && \
    echo '  echo "Flyctl auth configured"' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo 'exec python main.py' >> /start.sh && \
    chmod +x /start.sh

CMD ["/start.sh"]
