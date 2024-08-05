from python_postman.collection import Collection


def main():
    collection = Collection(
        "/Users/wry/github/python-postman/tests/CollectionExample.postman_collection.json"
    )

    # collection = Collection(
    #     "/Users/wry/github/python-postman/tests/EIA APIv2.postman_collection.json"
    # )

    # print(collection._variables)
    print("\n\n")
    print(collection._auth)
    print("\n\n")
    request = collection.get_request(name="FolderTwoSubOneReqOne")
    print(request)

    # print(request)

    # items = collection._items
    # print(items)
    # requests = collection._requests
    # print(requests)

    # folders = collection._folders
    # print(folders)

    # requests = collection._requests
    # print(requests)

    # environments_dir = "pypostman/environments"
    # environments: List[Environment] = postman._get_environments(dir=environments_dir)

    # collections_dir = "pypostman/collections"
    # collections: List[Collection] = postman._get_collections(dir=collections_dir)


if __name__ == "__main__":
    main()
