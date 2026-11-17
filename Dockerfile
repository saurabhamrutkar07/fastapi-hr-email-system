# Backend image: Python 3.12 + the pinned packages + the app code.
FROM python:3.12-slim 

# Print logs stright away, and dont write .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app 

# Packages first: Docker reuses this layer until requirements.txt changes,
# so a code-only change rebuilds in seconds 
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt 

# Then the code 
COPY app ./app 
COPY common ./common 
COPY migrations ./migrations 
COPY alembic.ini .

# Run as a normal user, not root 
RUN useradd --create-home appuser 
USER appuser 

EXPOSE 8000

# Bring the database up to date, then start the API.
# --proxy-headers: trust the real visitor IP that Nginx passes on (rate limits need it)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]