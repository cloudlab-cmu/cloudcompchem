# cloudcompchem
Goal of this repo is to provide a set of code for creating computational chemistry tools to be run on the cloud at ECL in collaboration with CMU. This will be done via a webserver that responds to requests by running DFT calculations.

# Details
`cloudcompchem` is provided as an application with both a command line interface (CLI) and a set of python bindings that can be used in additional application logic. The CLI can run both local calculations and spin up a webserver that serves calculation requests to the python bindings.

The web server is built on Flask, and has one primary endpoint (for now), `/energy`. The `/energy` endpoint serves to calculate the single point energy of a molecule and return the total and orbital energies (along with other metadata). A successful calculation returns a `200` OK, when run as a server, and gives a `400` Bad Request if any part of the input is malformed. It may also give a `401` Unauthorized if the user is either not logged in or provides an invalid auth token.

# Getting Started

## Installing Dependencies

Create a fresh virtual environment (e.g. with `conda`, `venv`, etc.). Once the environment has been built and activated, `pip install .` while in the application directory. For developers, go to the `cloudcompchem` directory and `pip install -r requirements-dev.txt`.

## Running locally

To test that it installed correctly, attempt to run it:
```sh
cloudcompchem serve
```

This will launch the web service locally on port 5000 with 4 workers. It should start up without errors.

You can modify the state of the web server with additional keyword arguments:
```sh
cloudcompchem serve --bind 0.0.0.0:5400 --workers 16
```
The above command directs the server to bind to port `5400` at local host (`0.0.0.0`) and increases the number of workers (threads) to `16`.

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

## Running locally from command line

To run an energy calculation from the command line, you may:
```sh
cloudcompchem energy input.json
```
where `input.json` is a structured file containing functional/basis set information along with molecule details.

### Input payload structure

To run an energy calculation, the input payload must be correctly specified. A typical input structure looks like:
```json
{
  "config": {
    "basis_set": "ccpvdz",
    "functional": "pbe,pbe",
  },
  "molecule": {
    "charge": 0,
    "spin_multiplicity": 1,
    "atoms": [
      {"position": [0., 0., 0.], "symbol": "H"},
      {"position": [0., 0., 1.], "symbol": "H"},
    ]
  }
}
```
This payload can be inputted as a body to a json HTTP request, or as a file to the command line invocation. The `basis_set` has to be specified according to `pyscf` specifications, and the `functional` value must be present in the `LibXC` library. Note that the `functional` value has two components separated by a comma (without a space) representing the exchange and correlation functionals separately.

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
