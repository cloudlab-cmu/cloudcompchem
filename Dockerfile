FROM python:3.12-slim

ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=${LOG_LEVEL}

# security updates
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
RUN apt-get install -y \
    # required by pyscf
    pkg-config libhdf5-dev gcc \
    # need git to pip install basis-set-exchange directly against the github repo
    # because the last released version doesn't support python3.12, which has since been addressed
    git

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
