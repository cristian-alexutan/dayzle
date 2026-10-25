FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# base.txt for production images, dev.txt for local development (see docker-compose.yml)
ARG REQUIREMENTS=base.txt
COPY requirements/ requirements/
RUN pip install -r requirements/${REQUIREMENTS}

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
