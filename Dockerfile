FROM python:3.11.8-bullseye

ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=${LOG_LEVEL}

# security updates
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

RUN python -m pip install --upgrade pip

WORKDIR /app

COPY ./setup.* ./
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./cloudcompchem ./cloudcompchem

# Prepare the environment for Flask
ENV FLASK_ENV production
ENV FLASK_APP /app/server.py

# Run the flask app!
EXPOSE 5000
CMD gunicorn -b 0.0.0.0:5000 "wsgi:app" --log-level=${LOG_LEVEL} --timeout=90 --workers=8 --chdir /app/cloudcompchem
