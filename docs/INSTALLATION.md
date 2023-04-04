## Installation

### Development Setup

Clone the repo:

```
git clone https://github.com/fluidefi/fluidefi-caspernet-analytics-tools.git
cd fluidefi-caspernet-analytics-tools
```

Checkout develop branch:

```
git checkout develop
```

#### Installing CSPR Summarizers

navigate to app

```bash
cd app
```

Create a new python virtual environment and activate the environment

```
python3 -m venv venv
activate venv/source/bin
```

Install dependencies into virtual environment

```
python3 -m pip install -r requirements.txt
```

In the main directory, find the environment example file .env.example and copy the contents of the file to a .env. It is used for application configuration. Be sure to use the version in the same repository branch that is being tested.

```
cp .env.example .env
```

Modify the .env file to include the database location and credentials. These should most likely be the same as those used for the FLUIDEFI Aggregator.

Run migrations to create the tables

```
python manage.py migrate
```

or alternatively create them manually by running [this script](./docs/queries.sql).

Lastly, run the summarizers

Navigate back to app

```bash
cd app
```

and run the services

```bash
python3 block_summarizer.py
```

```bash
python3 hourly_summarizer.py
```

#### Installing the API

similarly to CSPR Summarizers installation, navigate to api

```bash
cd api
```

Activate the previously created virtual environment:

```
python3 -m venv venv
activate venv/source/bin
```

The environment setup for the API was already included with CSPR Summarizers environment setup.

Run migrations to create the tables

```
python manage.py migrate
```

For authentication, you will need to create a supper user by running:

```
python3 manage.py createsuperuser
```

You will be asked to fill in username, email, and password.

Lastly, run the app

```bash
python3 manage.py runserver 0.0.0.0:8080
```

### Installation via Docker

If you haven't yet configured your environment, find the environment example file .env.example and copy the contents of the file to a .env.

```
cp .env.example .env
```

Modify the .env file to include the database location and credentials. These should most likely be the same as those used for the FLUIDEFI Aggregator.

Now, you can run the two applications, summarizers and api, by simply running:

```bash
docker compose up --build
```
