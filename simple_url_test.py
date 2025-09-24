from python_postman.models.url import Url, QueryParam

# Test basic URL creation
url = Url(raw="https://example.com/test")
print(f"URL created: {url.protocol}://{'.'.join(url.host)}")

# Test query parameter
param = QueryParam("key", "value")
print(f"Query param: {param.key}={param.value}")

print("URL components test passed!")
