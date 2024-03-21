FROM python:3.11.8-bullseye

# Add all the python code we need to run the app.
RUN mkdir -p /opt/compchem_runtime/


ADD ./svc /opt/compchem_runtime
ADD ./cloudcompchem /opt/compchem_runtime/cloudcompchem
COPY ./setup.* /opt/compchem_runtime/
COPY ./requirements/common.txt /opt/compchem_runtime/common.txt
COPY ./requirements/deployment.txt /opt/compchem_runtime/requirements.txt

WORKDIR /opt/compchem_runtime

#################################################################
### Add any needed dependencies/libraries here.  Instructions ###
### on installing libraries on alpine linux can be found at:  ###
### https://wiki.alpinelinux.org/wiki/Package_management      ###
#################################################################

# security updates
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# if we do need anything, append this...
# DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#    mypkg \
#    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version - this can fix some installation issues
RUN python -m pip install -U pip

# Add ECL directory to pythonpath

ENV PYTHONPATH "${PYTHONPATH}:/opt/compchem_runtime"

# Install the requirements
RUN pip install -r requirements.txt

# Prepare the environment for Flask
ENV FLASK_ENV production
ENV FLASK_APP /opt/compchem_runtime/svc/app.py

# Run the flask app!
EXPOSE 5000
CMD gunicorn -b 0.0.0.0:5000 "wsgi:app" --log-level=INFO --timeout=90 --workers=8 --chdir /opt/compchem_runtime/
