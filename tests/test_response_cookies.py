"""Tests for Response cookie integration."""

import pytest
from python_postman.models.response import Response
from python_postman.models.header import Header
from python_postman.models.cookie import Cookie, CookieJar


class TestResponseCookies:
    """Test Response.get_cookies() method."""

    def test_get_cookies_from_headers(self):
        """Test extracting cookies from Set-Cookie headers."""
        headers = [
            Header(key="Set-Cookie", value="sessionid=abc123; Domain=example.com; Path=/"),
            Header(key="Set-Cookie", value="userid=user1; Secure; HttpOnly"),
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            headers=headers,
        )

        jar = response.get_cookies()

        assert len(jar) == 2
        session_cookie = jar.get("sessionid")
        assert session_cookie is not None
        assert session_cookie.value == "abc123"
        assert session_cookie.domain == "example.com"

        user_cookie = jar.get("userid")
        assert user_cookie is not None
        assert user_cookie.value == "user1"
        assert user_cookie.secure is True
        assert user_cookie.http_only is True

    def test_get_cookies_from_postman_array(self):
        """Test extracting cookies from Postman cookie array."""
        cookie_data = [
            {
                "name": "sessionid",
                "value": "abc123",
                "domain": "example.com",
                "path": "/",
            },
            {
                "name": "userid",
                "value": "user1",
                "secure": True,
                "httpOnly": True,
            },
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            cookie=cookie_data,
        )

        jar = response.get_cookies()

        assert len(jar) == 2
        session_cookie = jar.get("sessionid")
        assert session_cookie is not None
        assert session_cookie.value == "abc123"
        assert session_cookie.domain == "example.com"

        user_cookie = jar.get("userid")
        assert user_cookie is not None
        assert user_cookie.value == "user1"
        assert user_cookie.secure is True
        assert user_cookie.http_only is True

    def test_get_cookies_from_both_sources(self):
        """Test extracting cookies from both headers and Postman array."""
        headers = [
            Header(key="Set-Cookie", value="sessionid=abc123; Domain=example.com"),
        ]
        cookie_data = [
            {
                "name": "userid",
                "value": "user1",
                "domain": "example.com",
            },
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            headers=headers,
            cookie=cookie_data,
        )

        jar = response.get_cookies()

        assert len(jar) == 2
        assert jar.get("sessionid") is not None
        assert jar.get("userid") is not None

    def test_get_cookies_empty(self):
        """Test getting cookies when none exist."""
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
        )

        jar = response.get_cookies()

        assert len(jar) == 0

    def test_get_cookies_invalid_header(self):
        """Test that invalid Set-Cookie headers are skipped."""
        headers = [
            Header(key="Set-Cookie", value="sessionid=abc123"),
            Header(key="Set-Cookie", value="invalid_cookie_no_equals"),
            Header(key="Set-Cookie", value="userid=user1"),
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            headers=headers,
        )

        jar = response.get_cookies()

        # Should have 2 valid cookies, invalid one skipped
        assert len(jar) == 2
        assert jar.get("sessionid") is not None
        assert jar.get("userid") is not None

    def test_get_cookies_invalid_dict(self):
        """Test that invalid cookie dictionaries are skipped."""
        cookie_data = [
            {"name": "sessionid", "value": "abc123"},
            {"invalid": "data"},  # Missing required fields
            {"name": "userid", "value": "user1"},
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            cookie=cookie_data,
        )

        jar = response.get_cookies()

        # Should have 2 valid cookies, invalid one skipped
        assert len(jar) == 2
        assert jar.get("sessionid") is not None
        assert jar.get("userid") is not None

    def test_get_cookies_case_insensitive_header(self):
        """Test that Set-Cookie header matching is case-insensitive."""
        headers = [
            Header(key="set-cookie", value="sessionid=abc123"),
            Header(key="SET-COOKIE", value="userid=user1"),
            Header(key="Content-Type", value="application/json"),
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            headers=headers,
        )

        jar = response.get_cookies()

        assert len(jar) == 2
        assert jar.get("sessionid") is not None
        assert jar.get("userid") is not None

    def test_get_cookies_duplicate_names(self):
        """Test handling duplicate cookie names (last one wins)."""
        headers = [
            Header(key="Set-Cookie", value="sessionid=abc123"),
            Header(key="Set-Cookie", value="sessionid=xyz789"),
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            headers=headers,
        )

        jar = response.get_cookies()

        # CookieJar.add() replaces cookies with same name/domain/path
        assert len(jar) == 1
        cookie = jar.get("sessionid")
        assert cookie.value == "xyz789"

    def test_get_cookies_with_complex_attributes(self):
        """Test extracting cookies with complex attributes."""
        headers = [
            Header(
                key="Set-Cookie",
                value="sessionid=abc123; Domain=.example.com; Path=/api; Expires=Wed, 21 Oct 2025 07:28:00 GMT; Max-Age=3600; Secure; HttpOnly; SameSite=Strict",
            ),
        ]
        response = Response(
            name="Test Response",
            status="OK",
            code=200,
            headers=headers,
        )

        jar = response.get_cookies()

        assert len(jar) == 1
        cookie = jar.get("sessionid")
        assert cookie is not None
        assert cookie.value == "abc123"
        assert cookie.domain == ".example.com"
        assert cookie.path == "/api"
        assert cookie.expires is not None
        assert cookie.max_age == 3600
        assert cookie.secure is True
        assert cookie.http_only is True
        assert cookie.same_site == "Strict"

    def test_get_cookies_integration_with_from_dict(self):
        """Test that cookies work with Response.from_dict()."""
        data = {
            "name": "Test Response",
            "status": "OK",
            "code": 200,
            "header": [
                {"key": "Set-Cookie", "value": "sessionid=abc123"},
            ],
            "cookie": [
                {"name": "userid", "value": "user1"},
            ],
        }
        response = Response.from_dict(data)

        jar = response.get_cookies()

        assert len(jar) == 2
        assert jar.get("sessionid") is not None
        assert jar.get("userid") is not None

