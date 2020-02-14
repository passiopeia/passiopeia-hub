"""
Handling the next part of the URL
"""
from typing import Optional, List

from django.http import HttpRequest


def _get_next(next_urls: List[str]) -> Optional[str]:
    """
    Extract the next URL from the list of candidates

    :param List[str] next_urls: List of URLs to check
    :rtype: Optional[str]
    :return: A URL or None if invalid
    """
    if len(next_urls) < 1:
        return None
    next_url = next_urls[0]
    if next_url is None:
        return None
    next_url = next_url.strip()
    if next_url.startswith('/'):
        return next_url
    return None


def get_next(request: HttpRequest) -> Optional[str]:
    """
    Get the next URL from Request object

    Priority:
        1. POST
        2. GET

    :param HttpRequest request: The Request Object
    :rtype: Optional[str]
    :returns: The next URL or "None", if invalid or not set
    """
    for request_type in [request.POST, request.GET]:
        next_vars = request_type.getlist('next')
        result = _get_next(next_vars)
        if result is not None:
            break
    return result
