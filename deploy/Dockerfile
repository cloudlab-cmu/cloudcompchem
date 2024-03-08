FROM python:3.8-alpine

# Add all the python code we need to run the app.
RUN mkdir -p /opt/tachyon_runtime/


COPY ./tachyon/svc/ /opt/tachyon_runtime/
COPY ./tachyon/constellation-sdk/ /opt/tachyon_runtime/
COPY ./tachyon/requirements/common.txt /opt/tachyon_runtime/common.txt
COPY ./tachyon/requirements/deployment.txt /opt/tachyon_runtime/requirements.txt

WORKDIR /opt/tachyon_runtime

# Upgrade pip to the latest version - this can fix some installation issues
RUN python -m pip install -U pip

#################################################################
### Add any needed dependencies/libraries here.  Instructions ###
### on installing libraries on alpine linux can be found at:  ###
### https://wiki.alpinelinux.org/wiki/Package_management      ###
#################################################################

# Install bind utils
RUN apk update && apk add bind-tools

# Add ECL directory to pythonpath

ENV PYTHONPATH "${PYTHONPATH}:/opt/tachyon_runtime/constellation-sdk"

# Install the requirements
RUN pip install -r requirements.txt

# Prepare the environment for Flask
ENV FLASK_ENV production
ENV FLASK_APP /opt/tachyon_runtime/svc/app.py

# Run the flask app!
EXPOSE 5000
CMD gunicorn -b 0.0.0.0:5000 "wsgi:app" --log-level=INFO --timeout=90 --workers=8 --chdir /opt/tachyon_runtime/
