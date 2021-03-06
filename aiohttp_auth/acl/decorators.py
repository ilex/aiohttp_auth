"""ACL middleware decorators."""

from functools import wraps
from aiohttp import web
from .acl import get_permitted


def acl_required(permission, context):
    """Create decorator to check given permission with given context.

    Return a decorator that checks if a user has the requested permission
    from the passed acl context.

    This function constructs a decorator that can be used to check a aiohttp's
    view for authorization before calling it. It uses the ``get_permission()``
    function to check the request against the passed permission and context. If
    the user does not have the correct permission to run this function, it
    raises ``web.HTTPForbidden``.

    Args:
        permission: The specific permission requested.
        context: Either a sequence of ACL tuples, or a callable that returns a
            sequence of ACL tuples. For more information on ACL tuples, see
            ``get_permission()``.

    Returns:
        A decorator which will check the request passed has the permission for
        the given context. The decorator will raise HTTPForbidden if the user
        does not have the correct permissions to access the view.
    """
    def decorator(func):

        @wraps(func)
        async def wrapper(*args):
            request = (args[-1].request
                       if isinstance(args[-1], web.View)
                       else args[-1])

            context_value = context() if callable(context) else context

            if await get_permitted(request, permission, context_value):
                return await func(*args)

            raise web.HTTPForbidden()

        return wrapper

    return decorator
