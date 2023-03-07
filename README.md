## Fluidefi Caspernet Analytics Tools

This repository contains a library of scripts that can be used to calculate pricing and summary information from the data aggregated by apps built with [fluidefi-caspernet-aggregator-tools](https://github.com/fluidefi/fluidefi-caspernet-aggregator-tools).

An application using these scripts / tools would be able to produce the following types of summary information:

- Liquidity Pool metrics, summarized on a per-block, hourly, daily, weekly and monthly frequency
- Weighted asset pricing using the rates found in onchain DEXes

Example Liquidity Pool metrics:
- open, close, high, low prices of underlying assets
- total rate of return for a liquidity pool in the specified period
- return from fees in the specified period
- return from the change in price of the underlying tokens in the specified period
- HODL return, defined as the return if tokens were held (not staked in a liquidity pool) in the specified period
- return from fees in the specified period, annualized
- cumulative total return metrics on investment in base_currency
- impermanent loss level - the percentage difference in portfolio value between staking tokens in an AMM and holding tokens in a wallet (fees are not taken
into account in this calculation)
- impermanent loss impact - The percentage difference in ROI between staking tokens in an AMM and holding tokens in a wallet (ees are not taken into
account in this calculation)
- volume & nubmer of transactions during the time period specified
- reserves & poolsize

### Quickstart (for a developer)
For QA purposes you can check [here](./docs/USAGE_OVERVIEW.md) how to run the whole services with only one command.
1. Clone the repo
```
git clone https://github.com/fluidefi/fluidefi-caspernet-analytics-tools.git
```
2. Navigate to the direcotry of the project
```
cd fluidefi-caspernet-analytics-tools
```
3. Create a python virtual environment, activate the virtual environment, and install pip.
```
python3 -m venv fl_agg_env
source fl_agg_env/bin/activate

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py

python3 -m pip install -r requirements.txt
```
4. Install the required Python packages using pip
``` 
pip install -r requirements.txt
```
5. Set environment variables for a database connection or update `settings.py` with database connection information.

For example:
```
DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'casper_database',
        'USER': 'postegres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': 5432,
    },
    "writer": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'casper_database',
        'USER': 'postegres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}
```

6. Run migrations to create the tables
``` 
python manage.py migrate
```
or alternatively create them manually by running [this script](./docs/queries.sql).

### Usage

1. Run one or both of the services
``` 
python block_summarizer.py
```
```
python hourly_summarizer.py
```

### Testing:

If you clone this repository directly, you can run the included unit tests with the python3 command:
```
cd tests/unit
python3 -m unittest
```

### Documentation:

Full documentation can be found in the [docs](https://github.com/fluidefi/fluidefi-caspernet-aggregator-tools/blob/master/docs/) folder.

* [Requirements](./docs/REQUIREMENTS.md)
* [Installation](./docs/INSTALLATION.md)
* [Usage Overview](./docs/USAGE_OVERVIEW.md)

The project was initiated with DEVxDAO proposal [#451](https://portal.devxdao.com/app/proposal/451)

Based on [casper.network](https://casper.network/en/network)

### Opensource components:
* [python](https://www.python.org/)
* [PostgreSQL](https://www.postgresql.org/)

### Contributing

Please see [Contributing Guidelines](https://github.com/fluidefi/fluidefi-caspernet-aggregator-tools/blob/master/CONTRIBUTING.md).

### Code of Conduct

Please see [Code of Conduct](https://github.com/fluidefi/fluidefi-caspernet-aggregator-tools/blob/master/CODE_OF_CONDUCT.md).

### License

This project is licensed under [MIT license](https://github.com/fluidefi/fluidefi-caspernet-aggregator-tools/blob/master/LICENSE.md).

### About us:
* [FLUIDEFI.COM](https://fluidefi.com/)

