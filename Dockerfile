# Stage 1: Build Frontend
FROM node:22-slim as frontend-builder
WORKDIR /app/frontend

# Install dependencies (cache optimized)
COPY frontend/package*.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build
# Output is in /app/frontend/dist

# Stage 2: Build Backend & Final Image
FROM python:3.9-slim
WORKDIR /app

# Install Backend Dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ .

# Copy Built Frontend Assets to Backend's static directory
# Backend logic expects: static/assets/ and static/index.html
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose API Port
EXPOSE 8000

# Run Application
CMD ["python", "main.py"]
