# Python Postman

**pypostman** is a command-line interface that allows to `automate` multiple api calls from postman collections, additionally it also allow you to `compress` and `save` the response to a local directory or to an AWS S3 bucket.
Thereby allowing you to manage your api calls using postman, then `automate` and `process` their response using python.

Example:

```
from pypostman.postman import Postman
from pypostman.modules.http import Request

postman = Postman()

collections_dir = "../collections"
collections = postman._get_collections(dir=collections_dir)
pokeapi_collection = postman._get_collection(name="PokeAPI", collections=collections)
pokeapi_requests = postman._get_requests(collection=pokeapi_collection)

def pokemon(self, **kwargs):
    # Make an API request.
    # The request name should match the Postman request name.
    name = "/pokemon"
    pokemon = postman._get_request(name=name, requests=pokeapi_requests)
    prepared_request: Request = Request(request=pokemon)
    prepared_request.set_path_vars(kwargs)
    prepared_request.set_params(kwargs)
    response = prepared_request.send
    return response
```
## What is Included?

- The **pypostman** source code.
- collections
  - Coinmarketcap.postman_collection.json
  - PokeAPI.postman_collection.json
- models
  - coinmarketcap_example.py
  - pokeapi_example.py

### Included Modules
- file.py
- http.py
- logger.py

## Installation

### Pythom >= 3.8

```
pip install python-postman
```

## How to Use It

See examples.