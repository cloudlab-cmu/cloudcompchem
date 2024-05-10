# cloudcompchem
Goal of this repo is to provide a set of code for creating computational chemistry tools to be run on the cloud at ECL in collaboration with CMU. This will be done via a webserver that responds to requests by running DFT calculations.

# Details
`cloudcompchem` is provided as an application with both a command line interface (CLI) and a set of python bindings that can be used in additional application logic. The CLI can run both local calculations and spin up a webserver that serves calculation requests to the python bindings.

The web server is built on Flask, and has one primary endpoint (for now), `/energy`. The `/energy` endpoint serves to calculate the single point energy of a molecule and return the total and orbital energies (along with other metadata). A successful calculation returns a `200` OK, when run as a server, and gives a `400` Bad Request if any part of the input is malformed. It may also give a `401` Unauthorized if the user is either not logged in or provides an invalid auth token.

# Getting Started

## Installing Dependencies

Create a fresh virtual environment (e.g. with `conda`, `venv`, etc.). Once the environment has been built and activated, `pip install -e .` while in the application directory. For developers, go to the `cloudcompchem` directory and `pip install -r requirements-dev.txt`.

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
      {"position": [0.0, 0.0, 0.0], "symbol": "H"},
      {"position": [0.0, 0.0, 1.0], "symbol": "H"},
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

## Asynchronous runtime

We use [celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) to power our
asynchronous runtime and enable long-running computations to run in the background without
blocking the user.

Celery requires a message broker to queue up the task definitions and store the results. We use
[redis](https://redis.io/) for that purpose. The easiest way to get `redis` running locally is through
Docker:

```
docker run --rm --name=cloudcompchem-celery-redis -d -p 6379:6379 redis
```

A simple example of a long-running task can be found in the `/aadd` (for *a*synchronous *add*) endpoint.
Let's make a call to it:

```
$ http --form POST :5000/aadd a=100 b=99
HTTP/1.1 200 OK
Connection: close
Content-Length: 53
Content-Type: application/json
Date: Fri, 26 Apr 2024 00:15:26 GMT
Server: gunicorn

{
    "result_id": "1d1347ab-0031-4f70-8d7a-b5f7c16e203f"
}
```

Because waiting for the actual results is prohibitive, what we get instead a `result_id`, a unique
identifier for the task that our asynchronous runtime should process. We can refer to this ID to
query the status of our computation:

```
http :5000/result/1d1347ab-0031-4f70-8d7a-b5f7c16e203f
HTTP/1.1 200 OK
Connection: close
Content-Length: 48
Content-Type: application/json
Date: Fri, 26 Apr 2024 00:18:56 GMT
Server: gunicorn

{
    "ready": false,
    "successful": false,
    "value": null
}
```

We need a `celery` worker to actually run the computation. Here's how we launch `celery`:

```
celery -A cloudcompchem.make_celery worker --loglevel INFO
```

The Celery worker connects to Redis and it sees that there's a message in queue corresponding to
the computation we requested earlier. It picks up the message from the queue and actually runs it
in a dedicated process. After some time, you should be able to query your results again:

```
http :5000/result/1d1347ab-0031-4f70-8d7a-b5f7c16e203f
HTTP/1.1 200 OK
Connection: close
Content-Length: 45
Content-Type: application/json
Date: Fri, 26 Apr 2024 00:20:44 GMT
Server: gunicorn

{
    "ready": true,
    "successful": true,
    "value": 199
}
```

If all of that sounded like a lot of steps, you might want to use
[docker-compose](https://docs.docker.com/compose/) to bring all of those services up with a single
command:

```
docker-compose up
```
