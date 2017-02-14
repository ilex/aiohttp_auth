"""Authentication decorators."""
from functools import wraps
from aiohttp import web
from .auth import get_auth


def auth_required(func):
    """Decorator to check if an user has been authenticated for this request.

    Allows views to be decorated like:

    .. code-block:: python

        @auth_required
        async def view_func(request):
            pass

    providing a simple means to ensure that whoever is calling the function
    has the correct authentication details.

    .. warning::

        .. versionchanged:: 0.2.0
            In versions prior 0.2.0 the ``web.HTTPForbidden`` was raised
            (status code 403) if user was not authenticated. Now the
            ``web.HTTPUnauthorized`` (status code 401) is raised to distinguish
            authentication error from authorization one.

    Args:
        func: Function object being decorated.

    Returns:
        A function object that will raise ``web.HTTPUnauthorized()`` if the
        passed request does not have the correct permissions to access the
        view.
    """
    @wraps(func)
    async def wrapper(*args):
        if (await get_auth(args[-1])) is None:
            raise web.HTTPUnauthorized()

        return await func(*args)

    return wrapper
