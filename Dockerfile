FROM python:3.13-slim

# Instalar dependencias de sistema que Playwright/Chromium necesita en Linux
# playwright install-deps resuelve esto automáticamente via apt
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar y instalar dependencias Python primero (capa cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Chromium en una ruta compartida accesible a usuarios sin privilegios.
# PLAYWRIGHT_BROWSERS_PATH sobreescribe el default (~/.cache/ms-playwright).
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN playwright install-deps chromium \
    && playwright install chromium \
    && chmod -R 755 /opt/playwright

# Usuario sin privilegios para ejecutar la app
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Copiar el código de la aplicación
COPY --chown=appuser:appuser app/ ./app/

EXPOSE 8090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "1"]
