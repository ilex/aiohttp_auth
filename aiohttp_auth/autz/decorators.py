"""Authorization decorators."""
from functools import wraps
from aiohttp import web
from . import autz


def autz_required(permission, context=None):
    """Create decorator to check if user has requested permission.

    This function constructs a decorator that can be used to check a aiohttp's
    view for authorization before calling it. It uses the ``autz.permit``
    function to check the request against the passed permission and context.
    If the user does not have the correct permission to run this function, it
    raises ``web.HTTPForbidden``.

    Note that context can be optional if authorization policy provides a way
    to specify global application context. Also context parameter can be used
    to override global context if it is provided by authorization policy.

    Note that some exceptions could be raised by certain policy while checking
    the permission.

    Args:
        permission: The specific permission requested.
        context: A context provided for checking permissions. Could be
            optional if authorization policy provides a way to specify a
            global application context.

    Returns:
        A decorator which will check the request passed has the permission for
        the given context. The decorator will raise ``web.HTTPForbidden`` if
        the user does not have the correct permissions to access the view.
    """
    def decorator(func):

        @wraps(func)
        async def wrapper(*args):
            request = args[-1]

            if await autz.permit(request, permission, context):
                return await func(*args)

            raise web.HTTPForbidden()

        return wrapper

    return decorator
