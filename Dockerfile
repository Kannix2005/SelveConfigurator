ARG BUILD_FROM

# ---------- Frontend build stage ----------
FROM node:18-alpine AS frontend-builder
WORKDIR /app

# Install and cache deps first
COPY frontend-src/package*.json ./
COPY frontend-src/yarn.lock* ./
RUN npm ci

# Build Quasar SPA
COPY frontend-src/ .
RUN npm run build


# ---------- Final runtime image ----------
FROM $BUILD_FROM

# Install Python runtime
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Backend dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Application sources
COPY run.py ./
COPY run.sh ./
COPY config.yaml ./
COPY index.html ./

# Built frontend bundle served by Flask
COPY --from=frontend-builder /app/dist/spa ./frontend

RUN chmod a+x /app/run.sh

CMD [ "/app/run.sh" ]