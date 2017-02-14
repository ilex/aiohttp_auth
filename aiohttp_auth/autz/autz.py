"""Authorization middleware."""
from ..auth import get_auth
from .abc import AbstractAutzPolicy


AUTZ_POLICY_KEY = 'aiohttp_auth.autz.policy'


def autz_middleware(autz_policy):
    """Return authorization middleware factory.

    Return ``aiohttp_auth.autz`` middleware factory for use by the ``aiohttp``
    application object. This middleware can be used only with
    ``aiohttp_auth.auth`` middleware installed.

    The ``autz`` middleware provides follow interface to use in applications:

        - Using ``autz.permit`` coroutine.
        - Using ``autz.autz_required`` decorator for ``aiohttp`` handlers.

    Note that the recomended way to initialize this middleware is through
    ``aiohttp_auth.autz.setup`` or ``aiohttp_auth.setup`` functions. As the
    ``autz`` middleware can be used only with authentication
    ``aiohttp_auth.auth`` middleware it is preferred to use
    ``aiohttp_auth.setup``.

    Args:
        autz_policy: a subclass of
            ``aiohttp_auth.autz.abc.AbstractAutzPolicy``.

    Returns:
        An ``aiohttp`` middleware factory.
    """
    assert isinstance(autz_policy, AbstractAutzPolicy)

    async def _middleware_factory(app, handler):

        async def _middleware_handler(request):
            # Save the policy in the request
            request[AUTZ_POLICY_KEY] = autz_policy

            # Call the next handler in the chain
            return await handler(request)

        return _middleware_handler

    return _middleware_factory


async def permit(request, permission, context=None):
    """Check if permission is allowed for given request with given context.

    The authorization checking is provided by authorization policy which is
    set by setup function. The nature of permission and context is also
    determined by the given policy.

    Note that this coroutine uses ``aiohttp_auth.auth.get_auth`` coroutine
    to determine ``user_identity`` for given request. So that middleware
    should be installed too.

    Note that some additional exceptions could be raised by certain policy
    while checking the permission.

    Args:
        request: aiohttp ``Request`` object.
        permission: The specific permission requested.
        context: A context provided for checking permissions. Could be
            optional if authorization policy provides a way to specify a
            global application context.

    Returns:
        ``True`` if permission is allowed ``False`` otherwise.

    Raises:
        RuntimeError: If ``auth`` or ``autz`` middleware is not installed.
    """
    user_identity = await get_auth(request)

    policy = request.get(AUTZ_POLICY_KEY, None)
    if policy is None:
        raise RuntimeError('autz_middleware not installed.')

    return await policy.permit(user_identity, permission, context)


def setup(app, autz_policy):
    """Setup an authorization middleware in ``aiohttp`` fashion.

    Note that ``aiohttp_auth.auth`` middleware should be installed too to use
    ``autz`` middleware. So the preferred way to install this middleware is to
    use global ``aiohttp_auth.setup`` function.

    Args:
        app: aiohttp ``Application`` object.
        autz_policy: A subclass of
            ``aiohttp_auth.autz.abc.AbstractAutzPolicy``.
    """
    app.middlewares.append(autz_middleware(autz_policy))
