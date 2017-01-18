import pytest
from aiohttp import web
import aiohttp_session
from aiohttp_auth import autz, auth
from aiohttp_auth.autz import autz_required
from aiohttp_auth.autz.abc import AbstractAutzPolicy
from utils import assert_response


class CustomAutzPolicy(AbstractAutzPolicy):

    def __init__(self, admin_user_identity):
        self.admin_user_identity = admin_user_identity

    async def permit(self, user_identity, permission, context=None):
        if permission == 'admin':
            if user_identity == self.admin_user_identity:
                return True

            return False

        return True


@pytest.fixture
def app(loop):
    """Default app fixture for tests."""
    async def handler_remember(request):
        user_identity = request.match_info['user']
        await auth.remember(request, user_identity)
        return web.Response(text='remember')

    @autz_required('admin')
    async def handler_admin(request):
        return web.Response(text='admin')

    @autz_required('guest')
    async def handler_guest(request):
        return web.Response(text='guest')

    application = web.Application(loop=loop)

    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    policy = auth.SessionTktAuthentication(secret, 15, cookie_name='auth')

    aiohttp_session.setup(application, storage)
    auth.setup(application, policy)

    autz_policy = CustomAutzPolicy(admin_user_identity='alex')
    autz.setup(application, autz_policy)

    application.router.add_get('/remember/{user}', handler_remember)
    application.router.add_get('/admin', handler_admin)
    application.router.add_get('/guest', handler_guest)

    yield application


async def test_autz_custom_policy_with_alex_identity(app, client):

    cli = await client(app)

    await assert_response(cli.get('/remember/alex'), 'remember')
    await assert_response(cli.get('/admin'), 'admin')
    await assert_response(cli.get('/guest'), 'guest')


async def test_autz_custom_policy_with_bob_identity(app, client):

    cli = await client(app)

    await assert_response(cli.get('/remember/bob'), 'remember')
    await assert_response(cli.get('/guest'), 'guest')

    response = await cli.get('/admin')
    assert response.status == 403
