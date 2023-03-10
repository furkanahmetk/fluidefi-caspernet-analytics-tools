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

Create a new python virtual environment and activate

```
python3 -m venv venv
activate venv/source/bin
```

Install dependencies into virtual environment

```
python3 -m pip install -r requirements.txt
```

### Setup Django (1 time only)

Find the environment example file .env.example and copy the contents of the file to a .env. It is used for applciation configuration. Be sure to use the version in the same repository branch that is being tested.
```
cp .env.example .env
```
