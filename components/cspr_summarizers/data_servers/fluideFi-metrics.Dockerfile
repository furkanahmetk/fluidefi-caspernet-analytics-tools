FROM python:3.9-bullseye as fluidefi-metrics

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# installing dependecies for installing python packages
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN apt update -y && apt install -y build-essential libpq-dev
RUN pip install psycopg2-binary --no-binary psycopg2-binary

# installing packages
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN [ "python3", "-m", "pip", "install", "-r", "requirements.txt" ]


# copy general common files
COPY ./__init__.py ./__init__.py
COPY ./db_connection_manager.py ./db_connection_manager.py
COPY ./utils.py ./utils.py
COPY ./pricing ./pricing
COPY ./liquidity_pool/ ./liquidity_pool/
COPY ./misc ./misc