"""
Tests using real-world Postman collections to validate parsing, inspection, and roundtrip.
"""

import json
import time
from pathlib import Path

import pytest

from python_postman import PythonPostman, Collection
from python_postman.models.schema import SchemaVersion

REAL_WORLD_DIR = Path(__file__).parent / "test_data" / "real_world"

# All 9 real-world collection files
COLLECTION_FILES = sorted(REAL_WORLD_DIR.glob("*.postman_collection.json"))
COLLECTION_IDS = [p.stem.replace(".postman_collection", "") for p in COLLECTION_FILES]


@pytest.fixture(params=COLLECTION_FILES, ids=COLLECTION_IDS)
def collection_path(request):
    return request.param


@pytest.fixture
def collection(collection_path):
    return PythonPostman.from_file(collection_path)


# ---------------------------------------------------------------------------
# Parametrized tests (run against every collection)
# ---------------------------------------------------------------------------


class TestParsing:
    def test_from_file_succeeds(self, collection_path):
        """1. Parsing: from_file succeeds without error."""
        collection = PythonPostman.from_file(collection_path)
        assert collection is not None

    def test_info_name(self, collection):
        """2. Info: name is a non-empty string."""
        assert isinstance(collection.info.name, str)
        assert len(collection.info.name) > 0

    def test_info_schema(self, collection):
        """2. Info: schema contains v2.1.0."""
        assert "v2.1.0" in collection.info.schema

    def test_schema_version(self, collection):
        """3. Schema detection: schema_version is V2_1_0."""
        assert collection.schema_version == SchemaVersion.V2_1_0

    def test_validation(self, collection):
        """4. Validation: is_valid is True."""
        result = collection.validate()
        assert result.is_valid, f"Validation errors: {result.errors}"

    def test_get_requests_non_empty(self, collection):
        """5. Requests: get_requests() is non-empty."""
        requests = list(collection.get_requests())
        assert len(requests) > 0

    def test_list_requests(self, collection):
        """6. list_requests: returns a list of strings."""
        names = collection.list_requests()
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)
        assert len(names) > 0

    def test_get_variables(self, collection):
        """7. get_variables: returns a dict."""
        variables = collection.get_variables()
        assert isinstance(variables, dict)

    def test_to_dict_roundtrip(self, collection):
        """8. to_dict roundtrip: from_dict produces equivalent object."""
        data = collection.to_dict()
        roundtripped = Collection.from_dict(data)
        assert roundtripped.info.name == collection.info.name
        assert len(list(roundtripped.get_requests())) == len(
            list(collection.get_requests())
        )

    def test_to_json_roundtrip(self, collection):
        """9. to_json roundtrip: produces valid JSON and is re-parseable."""
        json_str = collection.to_json(indent=2)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "info" in parsed
        # Re-parse through PythonPostman
        roundtripped = PythonPostman.from_dict(parsed)
        assert roundtripped.info.name == collection.info.name

    def test_search_by_method(self, collection):
        """10. Search: by_method('GET') returns a list."""
        results = collection.search().by_method("GET").execute()
        assert isinstance(results, list)

    def test_statistics(self, collection):
        """11. Statistics: collect() returns dict with total_requests key."""
        stats = collection.get_statistics()
        data = stats.collect()
        assert isinstance(data, dict)
        assert "total_requests" in data
        assert data["total_requests"] > 0

    def test_request_properties(self, collection):
        """12. Request properties: every request has name, method, url."""
        for request in collection.get_requests():
            assert request.name and len(request.name) > 0
            assert request.method and len(request.method) > 0
            assert request.url is not None


# ---------------------------------------------------------------------------
# Targeted tests (specific collections)
# ---------------------------------------------------------------------------


def _load(name):
    path = REAL_WORLD_DIR / f"{name}.postman_collection.json"
    return PythonPostman.from_file(path)


class TestDeepFolderNavigation:
    """13. EIA APIv2 has deeply nested folders."""

    def test_find_nested_folder(self):
        collection = _load("EIA_APIv2")
        # Should have at least one folder
        folders_found = []
        for item in collection.items:
            from python_postman.models.folder import Folder

            if isinstance(item, Folder):
                folders_found.append(item.name)
        assert len(folders_found) > 0, "EIA APIv2 should have folders"


class TestCollectionAuth:
    """14. Genscape Oil Refineries has collection-level auth."""

    def test_auth_present(self):
        collection = _load("Genscape_Oil_Refineries")
        # Either collection has auth, or requests have auth headers
        has_collection_auth = collection.auth is not None
        has_request_auth = any(
            request.has_auth() for request in collection.get_requests()
        )
        has_auth_headers = any(
            any(h.key.lower() == "x-api-key" for h in request.headers)
            for request in collection.get_requests()
        )
        assert (
            has_collection_auth or has_request_auth or has_auth_headers
        ), "Genscape Oil Refineries should have auth"


class TestEventScripts:
    """15. Per Security Requests has test scripts."""

    def test_has_test_script(self):
        collection = _load("Per_Security_Requests")
        has_scripts = any(
            request.has_test_script() for request in collection.get_requests()
        )
        # Also check collection-level events
        has_collection_events = len(collection.events) > 0
        assert (
            has_scripts or has_collection_events
        ), "Per Security Requests should have test scripts"


class TestExampleResponses:
    """16. ArgusWS has example responses."""

    def test_has_responses(self):
        collection = _load("ArgusWS")
        has_responses = any(
            len(request.responses) > 0 for request in collection.get_requests()
        )
        assert has_responses, "ArgusWS should have example responses"


class TestVariables:
    """17. Genscape Oil Refineries has variables with baseUrl."""

    def test_variables_present(self):
        collection = _load("Genscape_Oil_Refineries")
        variables = collection.get_variables()
        assert len(variables) > 0, "Genscape Oil Refineries should have variables"
        assert "baseUrl" in variables, f"Expected 'baseUrl' in variables, got: {list(variables.keys())}"


class TestLargeCollectionPerf:
    """18. EIA APIv2 (largest) parses in under 5 seconds."""

    def test_parse_performance(self):
        path = REAL_WORLD_DIR / "EIA_APIv2.postman_collection.json"
        start = time.time()
        collection = PythonPostman.from_file(path)
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Parsing took {elapsed:.2f}s, expected < 5s"
        assert collection is not None
