"""
Custom exceptions for the Flightradar24 API client.
"""

class FR24Error(Exception):
    """Base exception for all Flightradar24 API errors."""
    pass

class FR24AuthenticationError(FR24Error):
    """Exception raised for authentication errors."""
    pass

class FR24RateLimitError(FR24Error):
    """Exception raised when rate limit is exceeded."""
    pass

class FR24NotFoundError(FR24Error):
    """Exception raised when a resource is not found."""
    pass

class FR24ServerError(FR24Error):
    """Exception raised for server errors."""
    pass

class FR24ClientError(FR24Error):
    """Exception raised for client errors."""
    pass

class FR24ValidationError(FR24Error):
    """Exception raised for validation errors."""
    pass

class FR24ConnectionError(FR24Error):
    """Exception raised for connection errors."""
    pass 