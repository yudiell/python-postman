from typing import List

from pypostman import postman
from .environment import Environment
from .collection import Collection


def main():
    environments_dir = "pypostman/environments"
    environments: List[Environment] = postman._get_environments(dir=environments_dir)

    collections_dir = "pypostman/collections"
    collections: List[Collection] = postman._get_collections(dir=collections_dir)


if __name__ == "__main__":
    main()
