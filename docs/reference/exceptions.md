# Exceptions Reference

Pyfr24 includes a comprehensive set of custom exceptions for better error handling.

## Base Exception

### FR24Error
Base exception class for all Pyfr24 errors.

```python
from pyfr24 import FR24Error

try:
    # API call
except FR24Error as e:
    print(f"Pyfr24 error: {e}")
```

## Authentication Errors

### FR24AuthenticationError
Raised when authentication fails or access is forbidden.

```python
from pyfr24 import FR24AuthenticationError

try:
    api = FR24API("invalid_token")
except FR24AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

Common causes:
- Invalid API token
- Expired token
- Missing token
- Insufficient permissions

## Resource Errors

### FR24NotFoundError
Raised when a requested resource is not found.

```python
from pyfr24 import FR24NotFoundError

try:
    tracks = api.get_flight_tracks("invalid_id")
except FR24NotFoundError as e:
    print(f"Flight not found: {e}")
```

Common cases:
- Invalid flight ID
- Non-existent flight number
- Invalid aircraft registration
- Invalid airport/airline code

## Rate Limiting

### FR24RateLimitError
Raised when API rate limits are exceeded.

```python
from pyfr24 import FR24RateLimitError

try:
    # Multiple API calls
except FR24RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
```

Best practices:
- Implement exponential backoff
- Cache frequently accessed data
- Batch requests when possible

## Server Errors

### FR24ServerError
Raised when the API server encounters an error.

```python
from pyfr24 import FR24ServerError

try:
    # API call
except FR24ServerError as e:
    print(f"Server error: {e}")
```

Common status codes:
- 500: Internal Server Error
- 502: Bad Gateway
- 503: Service Unavailable
- 504: Gateway Timeout

## Client Errors

### FR24ClientError
Raised for client-side errors (4xx status codes).

```python
from pyfr24 import FR24ClientError

try:
    # API call
except FR24ClientError as e:
    print(f"Client error: {e}")
```

Common status codes:
- 400: Bad Request
- 404: Not Found
- 422: Validation Error

## Validation Errors

### FR24ValidationError
Raised when input validation fails.

```python
from pyfr24 import FR24ValidationError

try:
    # API call with invalid parameters
except FR24ValidationError as e:
    print(f"Validation error: {e}")
```

Common cases:
- Invalid date format
- Invalid coordinates
- Missing required parameters
- Invalid parameter values

## Connection Errors

### FR24ConnectionError
Raised when network connection fails.

```python
from pyfr24 import FR24ConnectionError

try:
    # API call
except FR24ConnectionError as e:
    print(f"Connection error: {e}")
```

Common causes:
- Network timeout
- DNS resolution failure
- Connection refused
- SSL/TLS errors

## Error Handling Example

```python
from pyfr24 import (
    FR24API, FR24Error, FR24AuthenticationError, 
    FR24NotFoundError, FR24RateLimitError, 
    FR24ServerError, FR24ClientError,
    FR24ValidationError, FR24ConnectionError
)

def safe_api_call():
    try:
        api = FR24API(token)
        return api.get_flight_tracks(flight_id)
        
    except FR24AuthenticationError:
        print("Authentication failed")
        
    except FR24NotFoundError:
        print("Flight not found")
        
    except FR24RateLimitError:
        print("Rate limit exceeded")
        
    except FR24ServerError:
        print("Server error")
        
    except FR24ClientError as e:
        print(f"Client error: {e}")
        
    except FR24ValidationError as e:
        print(f"Invalid input: {e}")
        
    except FR24ConnectionError as e:
        print(f"Connection failed: {e}")
        
    except FR24Error as e:
        print(f"Other API error: {e}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
``` 