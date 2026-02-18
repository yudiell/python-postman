"""
Tests using real-world Postman collections to validate parsing, inspection, and roundtrip.
"""

import json
import time
from pathlib import Path

import pytest

from python_postman import PythonPostman, Collection
from python_postman.models.folder import Folder
from python_postman.models.schema import SchemaVersion

REAL_WORLD_DIR = Path(__file__).parent / "test_data" / "real_world"

# Real-world collection files
COLLECTION_FILES = sorted(REAL_WORLD_DIR.glob("*.postman_collection.json"))
COLLECTION_IDS = [p.stem.replace(".postman_collection", "") for p in COLLECTION_FILES]


@pytest.fixture(params=COLLECTION_FILES, ids=COLLECTION_IDS)
def collection_path(request):
    return request.param


@pytest.fixture
def collection(collection_path):
    return PythonPostman.from_file(collection_path)


def _load(name):
    path = REAL_WORLD_DIR / f"{name}.postman_collection.json"
    return PythonPostman.from_file(path)


# ---------------------------------------------------------------------------
# Parametrized tests (run against every collection)
# ---------------------------------------------------------------------------


class TestParsing:
    def test_from_file_succeeds(self, collection_path):
        """Parsing: from_file succeeds without error."""
        collection = PythonPostman.from_file(collection_path)
        assert collection is not None

    def test_info_name(self, collection):
        """Info: name is a non-empty string."""
        assert isinstance(collection.info.name, str)
        assert len(collection.info.name) > 0

    def test_info_schema(self, collection):
        """Info: schema contains v2.1.0."""
        assert "v2.1.0" in collection.info.schema

    def test_schema_version(self, collection):
        """Schema detection: schema_version is V2_1_0."""
        assert collection.schema_version == SchemaVersion.V2_1_0

    def test_validation(self, collection):
        """Validation: is_valid is True."""
        result = collection.validate()
        assert result.is_valid, f"Validation errors: {result.errors}"

    def test_get_requests_non_empty(self, collection):
        """Requests: get_requests() is non-empty."""
        requests = list(collection.get_requests())
        assert len(requests) > 0

    def test_list_requests(self, collection):
        """list_requests: returns a list of strings."""
        names = collection.list_requests()
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)
        assert len(names) > 0

    def test_get_variables(self, collection):
        """get_variables: returns a dict."""
        variables = collection.get_variables()
        assert isinstance(variables, dict)

    def test_to_dict_roundtrip(self, collection):
        """to_dict roundtrip: from_dict produces equivalent object."""
        data = collection.to_dict()
        roundtripped = Collection.from_dict(data)
        assert roundtripped.info.name == collection.info.name
        assert len(list(roundtripped.get_requests())) == len(
            list(collection.get_requests())
        )

    def test_to_json_roundtrip(self, collection):
        """to_json roundtrip: produces valid JSON and is re-parseable."""
        json_str = collection.to_json(indent=2)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "info" in parsed
        # Re-parse through PythonPostman
        roundtripped = PythonPostman.from_dict(parsed)
        assert roundtripped.info.name == collection.info.name

    def test_search_by_method(self, collection):
        """Search: by_method('GET') returns a list."""
        results = collection.search().by_method("GET").execute()
        assert isinstance(results, list)

    def test_statistics(self, collection):
        """Statistics: collect() returns dict with total_requests key."""
        stats = collection.get_statistics()
        data = stats.collect()
        assert isinstance(data, dict)
        assert "total_requests" in data
        assert data["total_requests"] > 0

    def test_request_properties(self, collection):
        """Request properties: every request has name, method, url."""
        for request in collection.get_requests():
            assert request.name and len(request.name) > 0
            assert request.method and len(request.method) > 0
            assert request.url is not None


# ---------------------------------------------------------------------------
# Targeted tests (specific collections)
# ---------------------------------------------------------------------------


class TestDeepFolderNavigation:
    """EIA APIv2 has deeply nested folders."""

    def test_find_nested_folder(self):
        collection = _load("EIA_APIv2")
        folders_found = []
        for item in collection.items:
            if isinstance(item, Folder):
                folders_found.append(item.name)
        assert len(folders_found) > 0, "EIA APIv2 should have folders"


class TestCollectionVariables:
    """Genscape Oil Storage has collection-level variables."""

    def test_variables_present(self):
        collection = _load("Genscape_Oil_Storage")
        variables = collection.get_variables()
        assert len(variables) > 0, "Genscape Oil Storage should have variables"


class TestLargeCollectionPerf:
    """EIA APIv2 (largest) parses in under 5 seconds."""

    def test_parse_performance(self):
        path = REAL_WORLD_DIR / "EIA_APIv2.postman_collection.json"
        start = time.time()
        collection = PythonPostman.from_file(path)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Parsing took {elapsed:.2f}s, expected < 5s"
        assert collection is not None
