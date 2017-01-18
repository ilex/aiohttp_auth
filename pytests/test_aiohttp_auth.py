import aiohttp_auth
import aiohttp_session
from aiohttp import web
from aiohttp_auth import autz, auth
from aiohttp_auth.autz.policy import acl


async def test_aiohttp_auth_middleware_setup(loop):
    app = web.Application(loop=loop)

    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    aiohttp_session.setup(app, storage)

    auth_policy = auth.SessionTktAuthentication(secret, 15,
                                                cookie_name='auth')

    class ACLAutzPolicy(acl.AbsractACLAutzPolicy):
        async def acl_groups(self, user_identity):
            return None  # pragma: no cover

    autz_policy = ACLAutzPolicy()

    aiohttp_auth.setup(app, auth_policy, autz_policy)

    middleware = auth.auth_middleware(auth_policy)
    assert app.middlewares[-2].__name__ == middleware.__name__

    middleware = autz.autz_middleware(autz_policy)
    assert app.middlewares[-1].__name__ == middleware.__name__
