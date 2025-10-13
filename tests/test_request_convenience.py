"""
Tests for Request convenience methods (REQ-007).
"""

import pytest
from python_postman.models.request import Request
from python_postman.models.url import Url
from python_postman.models.header import Header
from python_postman.models.body import Body
from python_postman.models.auth import Auth
from python_postman.models.event import Event


class TestRequestConvenienceMethods:
    """Test suite for Request convenience methods."""

    def test_has_body_with_raw_body(self):
        """Test has_body() returns True when request has raw body."""
        body = Body(mode="raw", raw="test body")
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            body=body
        )
        assert request.has_body() is True

    def test_has_body_with_formdata(self):
        """Test has_body() returns True when request has formdata."""
        body = Body(mode="formdata", formdata=[{"key": "field", "value": "value"}])
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            body=body
        )
        assert request.has_body() is True

    def test_has_body_with_urlencoded(self):
        """Test has_body() returns True when request has urlencoded data."""
        body = Body(mode="urlencoded", urlencoded=[{"key": "field", "value": "value"}])
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            body=body
        )
        assert request.has_body() is True

    def test_has_body_without_body(self):
        """Test has_body() returns False when request has no body."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.has_body() is False

    def test_has_body_with_empty_body(self):
        """Test has_body() returns False when body exists but is empty."""
        body = Body(mode="raw", raw="")
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            body=body
        )
        assert request.has_body() is False

    def test_has_auth_with_auth(self):
        """Test has_auth() returns True when request has authentication."""
        from python_postman.models.auth import AuthParameter
        auth = Auth(
            type="bearer",
            parameters=[AuthParameter(key="token", value="secret")]
        )
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            auth=auth
        )
        assert request.has_auth() is True

    def test_has_auth_without_auth(self):
        """Test has_auth() returns False when request has no authentication."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.has_auth() is False

    def test_has_headers_with_headers(self):
        """Test has_headers() returns True when request has headers."""
        headers = [
            Header(key="Content-Type", value="application/json"),
            Header(key="Authorization", value="Bearer token")
        ]
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            headers=headers
        )
        assert request.has_headers() is True

    def test_has_headers_without_headers(self):
        """Test has_headers() returns False when request has no headers."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.has_headers() is False

    def test_has_headers_with_empty_list(self):
        """Test has_headers() returns False when headers list is empty."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            headers=[]
        )
        assert request.has_headers() is False

    def test_has_prerequest_script_with_script(self):
        """Test has_prerequest_script() returns True when request has pre-request script."""
        events = [
            Event(listen="prerequest", script={"exec": ["console.log('pre-request')"]})
        ]
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            events=events
        )
        assert request.has_prerequest_script() is True

    def test_has_prerequest_script_without_script(self):
        """Test has_prerequest_script() returns False when request has no pre-request script."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.has_prerequest_script() is False

    def test_has_prerequest_script_with_only_test_script(self):
        """Test has_prerequest_script() returns False when only test script exists."""
        events = [
            Event(listen="test", script={"exec": ["pm.test('test', () => {})"]})
        ]
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            events=events
        )
        assert request.has_prerequest_script() is False

    def test_has_test_script_with_script(self):
        """Test has_test_script() returns True when request has test script."""
        events = [
            Event(listen="test", script={"exec": ["pm.test('test', () => {})"]})
        ]
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            events=events
        )
        assert request.has_test_script() is True

    def test_has_test_script_without_script(self):
        """Test has_test_script() returns False when request has no test script."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.has_test_script() is False

    def test_has_test_script_with_only_prerequest_script(self):
        """Test has_test_script() returns False when only pre-request script exists."""
        events = [
            Event(listen="prerequest", script={"exec": ["console.log('pre-request')"]})
        ]
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            events=events
        )
        assert request.has_test_script() is False

    def test_has_both_scripts(self):
        """Test request can have both pre-request and test scripts."""
        events = [
            Event(listen="prerequest", script={"exec": ["console.log('pre-request')"]}),
            Event(listen="test", script={"exec": ["pm.test('test', () => {})"]})
        ]
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            events=events
        )
        assert request.has_prerequest_script() is True
        assert request.has_test_script() is True

    def test_get_content_type_with_content_type_header(self):
        """Test get_content_type() returns Content-Type header value."""
        headers = [
            Header(key="Content-Type", value="application/json"),
            Header(key="Authorization", value="Bearer token")
        ]
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            headers=headers
        )
        assert request.get_content_type() == "application/json"

    def test_get_content_type_case_insensitive(self):
        """Test get_content_type() is case-insensitive."""
        headers = [
            Header(key="content-type", value="text/html"),
        ]
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            headers=headers
        )
        assert request.get_content_type() == "text/html"

    def test_get_content_type_mixed_case(self):
        """Test get_content_type() handles mixed case."""
        headers = [
            Header(key="CoNtEnT-TyPe", value="application/xml"),
        ]
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            headers=headers
        )
        assert request.get_content_type() == "application/xml"

    def test_get_content_type_without_content_type_header(self):
        """Test get_content_type() returns None when no Content-Type header."""
        headers = [
            Header(key="Authorization", value="Bearer token")
        ]
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            headers=headers
        )
        assert request.get_content_type() is None

    def test_get_content_type_no_headers(self):
        """Test get_content_type() returns None when no headers."""
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com")
        )
        assert request.get_content_type() is None

    def test_is_idempotent_get(self):
        """Test is_idempotent() returns True for GET."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is True

    def test_is_idempotent_head(self):
        """Test is_idempotent() returns True for HEAD."""
        request = Request(
            name="Test",
            method="HEAD",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is True

    def test_is_idempotent_put(self):
        """Test is_idempotent() returns True for PUT."""
        request = Request(
            name="Test",
            method="PUT",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is True

    def test_is_idempotent_delete(self):
        """Test is_idempotent() returns True for DELETE."""
        request = Request(
            name="Test",
            method="DELETE",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is True

    def test_is_idempotent_options(self):
        """Test is_idempotent() returns True for OPTIONS."""
        request = Request(
            name="Test",
            method="OPTIONS",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is True

    def test_is_idempotent_post(self):
        """Test is_idempotent() returns False for POST."""
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is False

    def test_is_idempotent_patch(self):
        """Test is_idempotent() returns False for PATCH."""
        request = Request(
            name="Test",
            method="PATCH",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is False

    def test_is_idempotent_case_insensitive(self):
        """Test is_idempotent() is case-insensitive."""
        request = Request(
            name="Test",
            method="get",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_idempotent() is True

    def test_is_cacheable_get(self):
        """Test is_cacheable() returns True for GET."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_cacheable() is True

    def test_is_cacheable_head(self):
        """Test is_cacheable() returns True for HEAD."""
        request = Request(
            name="Test",
            method="HEAD",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_cacheable() is True

    def test_is_cacheable_post(self):
        """Test is_cacheable() returns False for POST."""
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_cacheable() is False

    def test_is_cacheable_put(self):
        """Test is_cacheable() returns False for PUT."""
        request = Request(
            name="Test",
            method="PUT",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_cacheable() is False

    def test_is_cacheable_delete(self):
        """Test is_cacheable() returns False for DELETE."""
        request = Request(
            name="Test",
            method="DELETE",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_cacheable() is False

    def test_is_cacheable_case_insensitive(self):
        """Test is_cacheable() is case-insensitive."""
        request = Request(
            name="Test",
            method="head",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_cacheable() is True

    def test_is_safe_get(self):
        """Test is_safe() returns True for GET."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is True

    def test_is_safe_head(self):
        """Test is_safe() returns True for HEAD."""
        request = Request(
            name="Test",
            method="HEAD",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is True

    def test_is_safe_options(self):
        """Test is_safe() returns True for OPTIONS."""
        request = Request(
            name="Test",
            method="OPTIONS",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is True

    def test_is_safe_post(self):
        """Test is_safe() returns False for POST."""
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is False

    def test_is_safe_put(self):
        """Test is_safe() returns False for PUT."""
        request = Request(
            name="Test",
            method="PUT",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is False

    def test_is_safe_delete(self):
        """Test is_safe() returns False for DELETE."""
        request = Request(
            name="Test",
            method="DELETE",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is False

    def test_is_safe_patch(self):
        """Test is_safe() returns False for PATCH."""
        request = Request(
            name="Test",
            method="PATCH",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is False

    def test_is_safe_case_insensitive(self):
        """Test is_safe() is case-insensitive."""
        request = Request(
            name="Test",
            method="options",
            url=Url.from_string("https://api.example.com")
        )
        assert request.is_safe() is True

    def test_combined_convenience_methods(self):
        """Test using multiple convenience methods together."""
        from python_postman.models.auth import AuthParameter
        
        headers = [Header(key="Content-Type", value="application/json")]
        body = Body(mode="raw", raw='{"key": "value"}')
        auth = Auth(
            type="bearer",
            parameters=[AuthParameter(key="token", value="secret")]
        )
        events = [
            Event(listen="prerequest", script={"exec": ["console.log('pre-request')"]}),
            Event(listen="test", script={"exec": ["pm.test('test', () => {})"]})
        ]
        
        request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com"),
            headers=headers,
            body=body,
            auth=auth,
            events=events
        )
        
        # Verify all convenience methods
        assert request.has_body() is True
        assert request.has_auth() is True
        assert request.has_headers() is True
        assert request.has_prerequest_script() is True
        assert request.has_test_script() is True
        assert request.get_content_type() == "application/json"
        assert request.is_idempotent() is False
        assert request.is_cacheable() is False
        assert request.is_safe() is False

    def test_http_semantics_consistency(self):
        """Test that HTTP semantics are consistent across methods."""
        # GET should be safe, cacheable, and idempotent
        get_request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        assert get_request.is_safe() is True
        assert get_request.is_cacheable() is True
        assert get_request.is_idempotent() is True
        
        # POST should be none of these
        post_request = Request(
            name="Test",
            method="POST",
            url=Url.from_string("https://api.example.com")
        )
        assert post_request.is_safe() is False
        assert post_request.is_cacheable() is False
        assert post_request.is_idempotent() is False
        
        # PUT should be idempotent but not safe or cacheable
        put_request = Request(
            name="Test",
            method="PUT",
            url=Url.from_string("https://api.example.com")
        )
        assert put_request.is_safe() is False
        assert put_request.is_cacheable() is False
        assert put_request.is_idempotent() is True
