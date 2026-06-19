FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
