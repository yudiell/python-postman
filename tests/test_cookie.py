"""Tests for Cookie and CookieJar classes."""

import pytest
from datetime import datetime, timedelta
from python_postman.models.cookie import Cookie, CookieJar


class TestCookie:
    """Test Cookie class."""

    def test_cookie_initialization(self):
        """Test basic cookie initialization."""
        cookie = Cookie(
            name="session_id",
            value="abc123",
            domain="example.com",
            path="/",
            secure=True,
            http_only=True,
        )

        assert cookie.name == "session_id"
        assert cookie.value == "abc123"
        assert cookie.domain == "example.com"
        assert cookie.path == "/"
        assert cookie.secure is True
        assert cookie.http_only is True

    def test_cookie_from_header_simple(self):
        """Test parsing simple Set-Cookie header."""
        header = "sessionid=abc123"
        cookie = Cookie.from_header(header)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.path == "/"
        assert cookie.secure is False
        assert cookie.http_only is False

    def test_cookie_from_header_with_attributes(self):
        """Test parsing Set-Cookie header with attributes."""
        header = "sessionid=abc123; Domain=example.com; Path=/api; Secure; HttpOnly"
        cookie = Cookie.from_header(header)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.domain == "example.com"
        assert cookie.path == "/api"
        assert cookie.secure is True
        assert cookie.http_only is True

    def test_cookie_from_header_with_expires(self):
        """Test parsing Set-Cookie header with Expires."""
        header = "sessionid=abc123; Expires=Wed, 21 Oct 2025 07:28:00 GMT"
        cookie = Cookie.from_header(header)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.expires is not None
        assert cookie.expires.year == 2025
        assert cookie.expires.month == 10
        assert cookie.expires.day == 21

    def test_cookie_from_header_with_max_age(self):
        """Test parsing Set-Cookie header with Max-Age."""
        header = "sessionid=abc123; Max-Age=3600"
        cookie = Cookie.from_header(header)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.max_age == 3600

    def test_cookie_from_header_with_samesite(self):
        """Test parsing Set-Cookie header with SameSite."""
        header = "sessionid=abc123; SameSite=Strict"
        cookie = Cookie.from_header(header)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.same_site == "Strict"

    def test_cookie_from_header_complex(self):
        """Test parsing complex Set-Cookie header."""
        header = "sessionid=abc123; Domain=.example.com; Path=/; Expires=Wed, 21 Oct 2025 07:28:00 GMT; Secure; HttpOnly; SameSite=Lax"
        cookie = Cookie.from_header(header)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.domain == ".example.com"
        assert cookie.path == "/"
        assert cookie.expires is not None
        assert cookie.secure is True
        assert cookie.http_only is True
        assert cookie.same_site == "Lax"

    def test_cookie_from_header_invalid_empty(self):
        """Test parsing empty Set-Cookie header."""
        with pytest.raises(ValueError, match="empty value"):
            Cookie.from_header("")

    def test_cookie_from_header_invalid_no_equals(self):
        """Test parsing Set-Cookie header without equals sign."""
        with pytest.raises(ValueError, match="missing '='"):
            Cookie.from_header("sessionid")

    def test_cookie_from_dict(self):
        """Test parsing cookie from dictionary."""
        data = {
            "name": "sessionid",
            "value": "abc123",
            "domain": "example.com",
            "path": "/api",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Strict",
        }
        cookie = Cookie.from_dict(data)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.domain == "example.com"
        assert cookie.path == "/api"
        assert cookie.secure is True
        assert cookie.http_only is True
        assert cookie.same_site == "Strict"

    def test_cookie_from_dict_with_postman_fields(self):
        """Test parsing cookie from Postman format dictionary."""
        data = {
            "name": "sessionid",
            "value": "abc123",
            "domain": "example.com",
            "hostOnly": True,
            "session": False,
        }
        cookie = Cookie.from_dict(data)

        assert cookie.name == "sessionid"
        assert cookie.value == "abc123"
        assert cookie.domain == "example.com"
        assert cookie.host_only is True
        assert cookie.session is False

    def test_cookie_to_header_simple(self):
        """Test converting cookie to Set-Cookie header."""
        cookie = Cookie(name="sessionid", value="abc123")
        header = cookie.to_header()

        assert header == "sessionid=abc123; Path=/"

    def test_cookie_to_header_with_attributes(self):
        """Test converting cookie with attributes to Set-Cookie header."""
        cookie = Cookie(
            name="sessionid",
            value="abc123",
            domain="example.com",
            path="/api",
            secure=True,
            http_only=True,
        )
        header = cookie.to_header()

        assert "sessionid=abc123" in header
        assert "Domain=example.com" in header
        assert "Path=/api" in header
        assert "Secure" in header
        assert "HttpOnly" in header

    def test_cookie_to_header_with_expires(self):
        """Test converting cookie with expires to Set-Cookie header."""
        expires = datetime(2025, 10, 21, 7, 28, 0)
        cookie = Cookie(name="sessionid", value="abc123", expires=expires)
        header = cookie.to_header()

        assert "sessionid=abc123" in header
        assert "Expires=Tue, 21 Oct 2025 07:28:00 GMT" in header

    def test_cookie_to_header_with_max_age(self):
        """Test converting cookie with max-age to Set-Cookie header."""
        cookie = Cookie(name="sessionid", value="abc123", max_age=3600)
        header = cookie.to_header()

        assert "sessionid=abc123" in header
        assert "Max-Age=3600" in header

    def test_cookie_to_header_with_samesite(self):
        """Test converting cookie with SameSite to Set-Cookie header."""
        cookie = Cookie(name="sessionid", value="abc123", same_site="Strict")
        header = cookie.to_header()

        assert "sessionid=abc123" in header
        assert "SameSite=Strict" in header

    def test_cookie_to_dict(self):
        """Test converting cookie to dictionary."""
        cookie = Cookie(
            name="sessionid",
            value="abc123",
            domain="example.com",
            path="/api",
            secure=True,
            http_only=True,
        )
        data = cookie.to_dict()

        assert data["name"] == "sessionid"
        assert data["value"] == "abc123"
        assert data["domain"] == "example.com"
        assert data["path"] == "/api"
        assert data["secure"] is True
        assert data["httpOnly"] is True

    def test_cookie_to_dict_with_postman_fields(self):
        """Test converting cookie with Postman fields to dictionary."""
        cookie = Cookie(
            name="sessionid",
            value="abc123",
            host_only=True,
            session=False,
        )
        data = cookie.to_dict()

        assert data["name"] == "sessionid"
        assert data["value"] == "abc123"
        assert data["hostOnly"] is True
        assert data["session"] is False

    def test_cookie_is_expired_not_expired(self):
        """Test checking if cookie is not expired."""
        future = datetime.now() + timedelta(days=1)
        cookie = Cookie(name="sessionid", value="abc123", expires=future)

        assert cookie.is_expired() is False

    def test_cookie_is_expired_expired(self):
        """Test checking if cookie is expired."""
        past = datetime.now() - timedelta(days=1)
        cookie = Cookie(name="sessionid", value="abc123", expires=past)

        assert cookie.is_expired() is True

    def test_cookie_is_expired_no_expires(self):
        """Test checking if cookie without expires is not expired."""
        cookie = Cookie(name="sessionid", value="abc123")

        assert cookie.is_expired() is False

    def test_cookie_matches_domain_exact(self):
        """Test domain matching with exact match."""
        cookie = Cookie(name="sessionid", value="abc123", domain="example.com")

        assert cookie.matches_domain("example.com") is True
        assert cookie.matches_domain("other.com") is False

    def test_cookie_matches_domain_wildcard(self):
        """Test domain matching with wildcard domain."""
        cookie = Cookie(name="sessionid", value="abc123", domain=".example.com")

        assert cookie.matches_domain("example.com") is True
        assert cookie.matches_domain("www.example.com") is True
        assert cookie.matches_domain("api.example.com") is True
        assert cookie.matches_domain("other.com") is False

    def test_cookie_matches_domain_no_domain(self):
        """Test domain matching with no domain set."""
        cookie = Cookie(name="sessionid", value="abc123")

        assert cookie.matches_domain("example.com") is False

    def test_cookie_matches_path_exact(self):
        """Test path matching with exact match."""
        cookie = Cookie(name="sessionid", value="abc123", path="/api")

        assert cookie.matches_path("/api") is True
        assert cookie.matches_path("/other") is False

    def test_cookie_matches_path_prefix(self):
        """Test path matching with prefix match."""
        cookie = Cookie(name="sessionid", value="abc123", path="/api")

        assert cookie.matches_path("/api/users") is True
        assert cookie.matches_path("/api/posts") is True
        assert cookie.matches_path("/other") is False

    def test_cookie_matches_path_root(self):
        """Test path matching with root path."""
        cookie = Cookie(name="sessionid", value="abc123", path="/")

        assert cookie.matches_path("/") is True
        assert cookie.matches_path("/api") is True
        assert cookie.matches_path("/api/users") is True

    def test_cookie_equality(self):
        """Test cookie equality comparison."""
        cookie1 = Cookie(name="sessionid", value="abc123", domain="example.com", path="/")
        cookie2 = Cookie(name="sessionid", value="xyz789", domain="example.com", path="/")
        cookie3 = Cookie(name="other", value="abc123", domain="example.com", path="/")

        assert cookie1 == cookie2  # Same name, domain, path
        assert cookie1 != cookie3  # Different name

    def test_cookie_repr(self):
        """Test cookie string representation."""
        cookie = Cookie(name="sessionid", value="abc123", domain="example.com", path="/")
        repr_str = repr(cookie)

        assert "sessionid" in repr_str
        assert "example.com" in repr_str


class TestCookieJar:
    """Test CookieJar class."""

    def test_cookiejar_initialization(self):
        """Test CookieJar initialization."""
        jar = CookieJar()

        assert len(jar) == 0
        assert jar.cookies == []

    def test_cookiejar_add(self):
        """Test adding cookies to jar."""
        jar = CookieJar()
        cookie = Cookie(name="sessionid", value="abc123")

        jar.add(cookie)

        assert len(jar) == 1
        assert jar.cookies[0] == cookie

    def test_cookiejar_add_replace(self):
        """Test adding cookie replaces existing with same name/domain/path."""
        jar = CookieJar()
        cookie1 = Cookie(name="sessionid", value="abc123", domain="example.com", path="/")
        cookie2 = Cookie(name="sessionid", value="xyz789", domain="example.com", path="/")

        jar.add(cookie1)
        jar.add(cookie2)

        assert len(jar) == 1
        assert jar.cookies[0].value == "xyz789"

    def test_cookiejar_add_different_cookies(self):
        """Test adding different cookies."""
        jar = CookieJar()
        cookie1 = Cookie(name="sessionid", value="abc123", domain="example.com")
        cookie2 = Cookie(name="userid", value="user1", domain="example.com")

        jar.add(cookie1)
        jar.add(cookie2)

        assert len(jar) == 2

    def test_cookiejar_get_by_name(self):
        """Test getting cookie by name."""
        jar = CookieJar()
        cookie = Cookie(name="sessionid", value="abc123")
        jar.add(cookie)

        result = jar.get("sessionid")

        assert result is not None
        assert result.name == "sessionid"
        assert result.value == "abc123"

    def test_cookiejar_get_not_found(self):
        """Test getting non-existent cookie."""
        jar = CookieJar()

        result = jar.get("sessionid")

        assert result is None

    def test_cookiejar_get_with_domain(self):
        """Test getting cookie by name and domain."""
        jar = CookieJar()
        cookie1 = Cookie(name="sessionid", value="abc123", domain="example.com")
        cookie2 = Cookie(name="sessionid", value="xyz789", domain="other.com")
        jar.add(cookie1)
        jar.add(cookie2)

        result = jar.get("sessionid", domain="example.com")

        assert result is not None
        assert result.value == "abc123"

    def test_cookiejar_get_with_path(self):
        """Test getting cookie by name and path."""
        jar = CookieJar()
        cookie1 = Cookie(name="sessionid", value="abc123", path="/api")
        cookie2 = Cookie(name="sessionid", value="xyz789", path="/admin")
        jar.add(cookie1)
        jar.add(cookie2)

        result = jar.get("sessionid", path="/api")

        assert result is not None
        assert result.value == "abc123"

    def test_cookiejar_filter_by_domain(self):
        """Test filtering cookies by domain."""
        jar = CookieJar()
        cookie1 = Cookie(name="session1", value="abc", domain="example.com")
        cookie2 = Cookie(name="session2", value="def", domain="example.com")
        cookie3 = Cookie(name="session3", value="ghi", domain="other.com")
        jar.add(cookie1)
        jar.add(cookie2)
        jar.add(cookie3)

        results = jar.filter_by_domain("example.com")

        assert len(results) == 2
        assert all(c.domain == "example.com" for c in results)

    def test_cookiejar_filter_by_domain_wildcard(self):
        """Test filtering cookies by wildcard domain."""
        jar = CookieJar()
        cookie1 = Cookie(name="session1", value="abc", domain=".example.com")
        cookie2 = Cookie(name="session2", value="def", domain="other.com")
        jar.add(cookie1)
        jar.add(cookie2)

        results = jar.filter_by_domain("www.example.com")

        assert len(results) == 1
        assert results[0].name == "session1"

    def test_cookiejar_filter_by_path(self):
        """Test filtering cookies by path."""
        jar = CookieJar()
        cookie1 = Cookie(name="session1", value="abc", path="/api")
        cookie2 = Cookie(name="session2", value="def", path="/admin")
        cookie3 = Cookie(name="session3", value="ghi", path="/")
        jar.add(cookie1)
        jar.add(cookie2)
        jar.add(cookie3)

        results = jar.filter_by_path("/api/users")

        assert len(results) == 2  # /api and / match
        assert any(c.path == "/api" for c in results)
        assert any(c.path == "/" for c in results)

    def test_cookiejar_filter_for_request(self):
        """Test filtering cookies for a request."""
        jar = CookieJar()
        cookie1 = Cookie(name="session1", value="abc", domain="example.com", path="/")
        cookie2 = Cookie(name="session2", value="def", domain="other.com", path="/")
        cookie3 = Cookie(name="session3", value="ghi", domain="example.com", path="/api")
        jar.add(cookie1)
        jar.add(cookie2)
        jar.add(cookie3)

        results = jar.filter_for_request("example.com", "/api/users")

        assert len(results) == 2
        assert any(c.name == "session1" for c in results)
        assert any(c.name == "session3" for c in results)

    def test_cookiejar_filter_for_request_secure(self):
        """Test filtering cookies for secure request."""
        jar = CookieJar()
        cookie1 = Cookie(name="session1", value="abc", domain="example.com", secure=False)
        cookie2 = Cookie(name="session2", value="def", domain="example.com", secure=True)
        jar.add(cookie1)
        jar.add(cookie2)

        # Non-secure request
        results = jar.filter_for_request("example.com", "/", secure=False)
        assert len(results) == 1
        assert results[0].name == "session1"

        # Secure request
        results = jar.filter_for_request("example.com", "/", secure=True)
        assert len(results) == 2

    def test_cookiejar_filter_for_request_expired(self):
        """Test filtering excludes expired cookies."""
        jar = CookieJar()
        past = datetime.now() - timedelta(days=1)
        future = datetime.now() + timedelta(days=1)
        cookie1 = Cookie(name="session1", value="abc", domain="example.com", expires=past)
        cookie2 = Cookie(name="session2", value="def", domain="example.com", expires=future)
        jar.add(cookie1)
        jar.add(cookie2)

        results = jar.filter_for_request("example.com", "/")

        assert len(results) == 1
        assert results[0].name == "session2"

    def test_cookiejar_remove(self):
        """Test removing cookie from jar."""
        jar = CookieJar()
        cookie = Cookie(name="sessionid", value="abc123")
        jar.add(cookie)

        removed = jar.remove("sessionid")

        assert removed is True
        assert len(jar) == 0

    def test_cookiejar_remove_not_found(self):
        """Test removing non-existent cookie."""
        jar = CookieJar()

        removed = jar.remove("sessionid")

        assert removed is False

    def test_cookiejar_remove_with_domain(self):
        """Test removing cookie by name and domain."""
        jar = CookieJar()
        cookie1 = Cookie(name="sessionid", value="abc123", domain="example.com")
        cookie2 = Cookie(name="sessionid", value="xyz789", domain="other.com")
        jar.add(cookie1)
        jar.add(cookie2)

        removed = jar.remove("sessionid", domain="example.com")

        assert removed is True
        assert len(jar) == 1
        assert jar.cookies[0].domain == "other.com"

    def test_cookiejar_clear(self):
        """Test clearing all cookies."""
        jar = CookieJar()
        jar.add(Cookie(name="session1", value="abc"))
        jar.add(Cookie(name="session2", value="def"))

        jar.clear()

        assert len(jar) == 0

    def test_cookiejar_clear_expired(self):
        """Test clearing expired cookies."""
        jar = CookieJar()
        past = datetime.now() - timedelta(days=1)
        future = datetime.now() + timedelta(days=1)
        jar.add(Cookie(name="session1", value="abc", expires=past))
        jar.add(Cookie(name="session2", value="def", expires=past))
        jar.add(Cookie(name="session3", value="ghi", expires=future))

        removed_count = jar.clear_expired()

        assert removed_count == 2
        assert len(jar) == 1
        assert jar.cookies[0].name == "session3"

    def test_cookiejar_iteration(self):
        """Test iterating over cookies in jar."""
        jar = CookieJar()
        cookie1 = Cookie(name="session1", value="abc")
        cookie2 = Cookie(name="session2", value="def")
        jar.add(cookie1)
        jar.add(cookie2)

        cookies = list(jar)

        assert len(cookies) == 2
        assert cookie1 in cookies
        assert cookie2 in cookies

    def test_cookiejar_repr(self):
        """Test CookieJar string representation."""
        jar = CookieJar()
        jar.add(Cookie(name="session1", value="abc"))
        jar.add(Cookie(name="session2", value="def"))

        repr_str = repr(jar)

        assert "CookieJar" in repr_str
        assert "2" in repr_str

