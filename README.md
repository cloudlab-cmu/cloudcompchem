# cloudcompchem
Goal of this repo is to provide a set of code for creating computational chemistry tools to be run on the cloud at ECL in collaboration with CMU. This will be done via a webserver that responds to requests by running DFT calculations.

# Details
The web server is built on Flask, and has two primary endpoints, `/simulate` and `/results`. The `/simulate` endpoint serves to launch the calculation in a separate thread running on the same computer that the webserver is hosted on, and returns a `202` accepted with an `id` token to track the simulation progress. The `/results` endpoint queries the server for the completion status of the simulation, and returns a packet of metadata if the simulation is complete.

# Getting Started

## Installing Dependencies

Create a fresh virtual environment (e.g. with `conda`, `venv`, etc.). Once the environment has been built and activated, navigate to the `ECL-collab` folder, and call `pip install -r requirements/development.txt` to install all the project requirements.

## Running locally

To test that it installed correctly, attempt to run it:
```sh
FLASK_ENV=development gunicorn -b 0.0.0.0:5000 "wsgi:app" --log-level=DEBUG --chdir ./svc
```

This will launch the web service locally on port 5000.  It should start up without errors.

## Making requests

To check what the web service returns, you can use curl from a separate terminal to make the following
requests:

```sh
curl http://0.0.0.0:5000/health-check
```

or
```
curl http://localhost/health-check
```

## Running Tests

To make sure that all tests are passing, call:
```sh
pytest . -s
```

## Building Docker images
The webserver will be run through a docker image containing the server code and all the installed dependencies. To build the image, call from the `ECL-collab` folder:
```sh
./deploy/build.sh
```

This should build the docker image for you. If something goes wrong, make sure you have docker installed and running.

## To test your docker image

Once your docker image is built, you may run it locally via:
```sh
docker run -p 5000:5000 <image_name>
````

The image name will be printed by the build script in the previous step.

You may then send requests against port 5000 in the same way as with a locally running python version.  For example:
```sh
curl http://0.0.0.0:5000/health-check
```
