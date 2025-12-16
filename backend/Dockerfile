FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install tzdata for timezone support
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*


COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
