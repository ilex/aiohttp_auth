import aiohttp_auth
import aiohttp_session
from aiohttp import web
from aiohttp_auth import acl, auth


async def test_aiohttp_auth_middleware_setup(loop):
    app = web.Application(loop=loop)

    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    aiohttp_session.setup(app, storage)

    policy = auth.SessionTktAuthentication(secret, 15, cookie_name='auth')

    async def acl_groups_callback(user_id):
        pass

    aiohttp_auth.setup(app, policy, acl_groups_callback)

    middleware = auth.auth_middleware(policy)
    assert app.middlewares[-2].__name__ == middleware.__name__

    middleware = acl.acl_middleware(acl_groups_callback)
    assert app.middlewares[-1].__name__ == middleware.__name__
