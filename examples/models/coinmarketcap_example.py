import pendulum
import uuid

from pypostman.postman import Postman
from pypostman.modules.http import Request
from pypostman.modules.file import File
from pypostman.utils.cli import Cli
from pypostman.modules.logger import Log

postman = Postman()
cli = Cli()
log = Log()
ARGS = cli.parse_arguments()

# Postman collection and rerquest names should be used.
# Use a .env file for Auth.

collections_dir = "../collections"
collections = postman._get_collections(dir=collections_dir)
coinmarketcap_collection = postman._get_collection(
    name="Coinmarketcap", collections=collections
)
coinmarketcap_requests = postman._get_requests(collection=coinmarketcap_collection)


class Coinmarketcap:
    ## NOTE: This api requires an API key added to the .env file.
    def __init__(self) -> None:
        self.env = ARGS.environment
        self.bucket = "lovesoildata"
        self.s3_prefix = coinmarketcap_collection._variables.s3_prefix(env=self.env)

    def listings(self, **kwargs):
        # Make an API request.
        # The request name should match the Postman request name.
        name = "/listings/latest"
        listings = postman._get_request(name=name, requests=coinmarketcap_requests)
        prepared_request: Request = Request(request=listings)
        prepared_request.set_path_vars(kwargs)
        prepared_request.set_params(kwargs)
        response = prepared_request.send

        # Do something with the response(es)
        file: File = File()
        content_type = response.headers.get("Content-Type")
        file_ext = file.get_file_extension(content_type=content_type)
        filename = f"{uuid.uuid4().hex[:6].upper()}{file_ext}"
        source: str = file.write(payload=response, filename=filename)
        compressed: str = file.compress(source)

        # Do something with the file(s)
        # S3 authentication required
        file_timestamp = pendulum.now("UTC")
        key = f"{self.s3_prefix}/{filename}.gz|{file_timestamp}"
        file.s3_upload(filepath=compressed, bucket=self.bucket, key=key)
        log.info(f"Completed Process: {name} \n")


if __name__ == "__main__":
    coinmarketcap = Coinmarketcap()
    coinmarketcap.listings(circulating_supply_max=1000000000, limit=10, price_max=1)
