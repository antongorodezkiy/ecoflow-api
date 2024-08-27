# teamlead.pw.ecoflow.api

## Versions

`teamlead.pw.ecoflow.api` uses a modified version of [Semantic Versioning](https://semver.org) for all changes.

### Supported Python Versions

This library supports the following Python implementations:

- Python 3.10
- Python 3.11

## Installation

Install from PyPi using [pip](https://pip.pypa.io/en/latest/), a
package manager for Python.

```shell
pip3 install teamlead.pw.ecoflow.api
```

## Usage

### API Credentials

The `Ecoflow` client needs your Ecoflow API credentials. You can obtain `access_key` and `secret_key` on the page https://developer-eu.ecoflow.com/us/security and then pass these directly to the constructor.

### Make a Call

```python
from teamlead.pw.ecoflow.api import EcoflowApi

access_key = '123'
secret_key  = '456'
api = EcoflowApi(access_key = access_key, secret_key = secret_key)
api.set_logger(log)
response = api.get_mqtt_certification()
print(response)
```

### Enable Debug Logging

Log the API request and response data to the default or custom logger:

```python
api.debug_requests_on()
```
