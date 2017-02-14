import asyncio
from os import urandom
import pytest
from aiohttp import web
from aiohttp_auth import auth
import aiohttp_session
from utils import assert_response


@pytest.fixture
def app(loop):
    """Default app fixture for tests."""
    async def handler_remember(request):
        await auth.remember(request, 'some_user')
        return web.Response(text='remember')

    async def handler_auth(request):
        user_id = await auth.get_auth(request)
        assert user_id == 'some_user'
        assert user_id == await auth.get_auth(request)
        return web.Response(text='auth')

    async def handler_forget(request):
        user_id = await auth.get_auth(request)
        assert user_id == 'some_user'
        await auth.forget(request)
        return web.Response(text='forget')

    application = web.Application(loop=loop)
    application.router.add_get('/remember', handler_remember)
    application.router.add_get('/auth', handler_auth)
    application.router.add_get('/forget', handler_forget)

    yield application


async def test_middleware_setup(app):
    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 15, cookie_name='auth')

    auth.setup(app, policy)

    middleware = auth.auth_middleware(policy)

    assert app.middlewares[-1].__name__ == middleware.__name__


async def test_no_middleware_installed(app, client):
    async def handler_test(request):
        with pytest.raises(RuntimeError) as ex_info:
            await auth.get_auth(request)

        assert str(ex_info.value) == 'auth_middleware not installed'

        with pytest.raises(RuntimeError) as ex_info:
            await auth.remember(request, 'some_user')

        assert str(ex_info.value) == 'auth_middleware not installed'

        with pytest.raises(RuntimeError) as ex_info:
            await auth.forget(request)

        assert str(ex_info.value) == 'auth_middleware not installed'

        return web.Response(text='test')

    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_middleware_installed_no_session(app, client):
    async def handler_test(request):
        user_id = await auth.get_auth(request)
        assert user_id is None

        return web.Response(text='test')

    app.router.add_get('/test', handler_test)
    aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())
    auth.setup(app, auth.SessionTktAuthentication(urandom(16), 15))

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_middleware_stores_auth_in_session(app, client):
    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    policy = auth.SessionTktAuthentication(secret, 15, cookie_name='auth')

    aiohttp_session.setup(app, storage)
    auth.setup(app, policy)

    cli = await client(app)
    response = await cli.get('/remember')
    text = await response.text()
    assert text == 'remember'

    value = response.cookies.get(storage.cookie_name).value
    assert policy.cookie_name in value


async def test_middleware_gets_auth_from_session(app, client):
    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    policy = auth.SessionTktAuthentication(secret, 15, cookie_name='auth')

    aiohttp_session.setup(app, storage)
    auth.setup(app, policy)

    cli = await client(app)

    response = await cli.get('/remember')
    assert await response.text() == 'remember'

    await assert_response(cli.get('/auth'), 'auth')


async def test_middleware_stores_auth_in_cookie(app, client):
    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 15, cookie_name='auth')

    auth.setup(app, policy)

    cli = await client(app)

    response = await cli.get('/remember')
    text = await response.text()

    assert text == 'remember'
    assert policy.cookie_name in response.cookies


async def test_middleware_gets_auth_from_cookie(app, client):
    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 15, 2, cookie_name='auth')

    auth.setup(app, policy)

    cli = await client(app)

    response = await cli.get('/remember')
    text = await response.text()

    assert text == 'remember'
    assert policy.cookie_name in response.cookies

    assert_response(cli.get('/auth'), 'auth')


@pytest.mark.slow
async def test_middleware_reissues_ticket_auth(loop, app, client):
    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 15, 0, cookie_name='auth')

    auth.setup(app, policy)

    cli = await client(app)

    response = await cli.get('/remember')
    text = await response.text()

    assert text == 'remember'
    data = response.cookies[policy.cookie_name]

    # wait a second that the ticket value has changed
    await asyncio.sleep(1.0, loop=loop)

    response = await assert_response(cli.get('/auth'), 'auth')

    assert data != response.cookies[policy.cookie_name]


@pytest.mark.slow
async def test_middleware_doesnt_reissue_on_bad_response(loop, app, client):
    async def handler_bad_response(request):
        user_id = await auth.get_auth(request)
        assert user_id == 'some_user'
        return web.Response(status=400, text='bad_response')

    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 15, 0, cookie_name='auth')

    auth.setup(app, policy)
    app.router.add_get('/bad_response', handler_bad_response)

    cli = await client(app)

    response = await cli.get('/remember')
    text = await response.text()
    data = response.cookies[policy.cookie_name]

    assert text == 'remember'

    # wait a second that the ticket value has changed
    await asyncio.sleep(1.0, loop=loop)

    response = await assert_response(cli.get('/auth'), 'auth')

    assert data != response.cookies[policy.cookie_name]
    data = response.cookies[policy.cookie_name]

    await asyncio.sleep(1.0, loop=loop)

    response = await assert_response(cli.get('/bad_response'), 'bad_response')

    assert response.status == 400
    assert policy.cookie_name not in response.cookies


async def test_middleware_forget_with_session(app, client):
    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    policy = auth.SessionTktAuthentication(secret, 15, cookie_name='auth')

    aiohttp_session.setup(app, storage)
    auth.setup(app, policy)

    cli = await client(app)

    response = await assert_response(cli.get('/remember'), 'remember')
    value = response.cookies.get(storage.cookie_name).value
    assert policy.cookie_name in value

    response = await assert_response(cli.get('/forget'), 'forget')
    value = response.cookies.get(storage.cookie_name).value
    assert policy.cookie_name not in value

    with pytest.raises(AssertionError):
        await assert_response(cli.get('/auth'), 'auth')


async def test_middleware_forget_with_cookies(app, client):
    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 120, cookie_name='auth')

    auth.setup(app, policy)

    cli = await client(app)

    response = await assert_response(cli.get('/remember'), 'remember')
    assert policy.cookie_name in response.cookies

    response = await assert_response(cli.get('/forget'), 'forget')
    # aiohttp set cookie_name with empty string when del_cookie
    # assert policy.cookie_name not in response.cookies
    assert response.cookies[policy.cookie_name].value == ''

    with pytest.raises(AssertionError):
        await assert_response(cli.get('/auth'), 'auth')


async def test_middleware_auth_required_decorator(app, client):
    @auth.auth_required
    async def handler_test(request):
        return web.Response(text='test')

    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 120, cookie_name='auth')

    auth.setup(app, policy)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    response = await assert_response(cli.get('/test'), '401: Unauthorized')
    assert response.status == 401

    response = await assert_response(cli.get('/remember'), 'remember')

    response = await assert_response(cli.get('/test'), 'test')
    assert response.status == 200


async def test_middleware_cannot_store_auth_in_cookie_when_response_started(
        app, client):
    async def handler_test(request):
        await auth.remember(request, 'some_user')
        response = web.Response(text='test')
        await response.prepare(request)
        return response

    secret = b'01234567890abcdef'
    policy = auth.CookieTktAuthentication(secret, 15, cookie_name='auth')

    auth.setup(app, policy)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    response = await cli.get('/test')
    assert policy.cookie_name not in response.cookies
