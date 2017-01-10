import pytest
import aiohttp_session
from aiohttp import web
from aiohttp_auth import acl, auth
from aiohttp_auth.permissions import Group, Permission
from utils import assert_response


@pytest.fixture
def app(loop):
    """Default app fixture for tests."""
    async def handler_remember(request):
        await auth.remember(request, 'some_user')
        return web.Response(text='remember')

    application = web.Application(loop=loop)

    secret = b'01234567890abcdef'
    storage = aiohttp_session.SimpleCookieStorage()
    policy = auth.SessionTktAuthentication(secret, 15, cookie_name='auth')

    aiohttp_session.setup(application, storage)
    auth.setup(application, policy)

    application.router.add_get('/remember', handler_remember)

    yield application


async def _groups_callback(user_id):
    """Groups callback function that always returns two groups."""
    return ('group0', 'group1')


async def _auth_groups_callback(user_id):
    """Groups callback function that always returns two groups."""
    if user_id:
        return ('group0', 'group1')

    return ()


async def _none_groups_callback(user_id):
    """Groups callback function that always returns None."""
    return None


async def test_acl_middleware_setup(app):
    acl.setup(app, _groups_callback)

    middleware = acl.acl_middleware(_groups_callback)

    assert app.middlewares[-1].__name__ == middleware.__name__


async def test_no_middleware_installed(app, client):
    async def handler_test(request):
        with pytest.raises(RuntimeError):
            await acl.get_user_groups(request)

        return web.Response(text='test')

    app.router.add_get('/test', handler_test)
    cli = await client(app)

    await assert_response(cli.get('/remember'), 'remember')

    await assert_response(cli.get('/test'), 'test')


async def test_correct_groups_returned_for_authenticated_user(app, client):
    async def handler_test(request):
        groups = await acl.get_user_groups(request)

        assert 'group0' in groups
        assert 'group1' in groups
        assert 'some_user' in groups
        assert Group.Everyone in groups
        assert Group.AuthenticatedUser in groups

        return web.Response(text='test')

    acl.setup(app, _groups_callback)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/remember'), 'remember')

    await assert_response(cli.get('/test'), 'test')


async def test_correct_groups_returned_for_unauthenticated_user(app, client):
    async def handler_test(request):
        groups = await acl.get_user_groups(request)

        assert 'group0' in groups
        assert 'group1' in groups
        assert 'some_user' not in groups
        assert Group.Everyone in groups
        assert Group.AuthenticatedUser not in groups

        return web.Response(text='test')

    acl.setup(app, _groups_callback)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_no_groups_if_none_returned_from_callback(app, client):
    async def handler_test(request):
        groups = await acl.get_user_groups(request)
        assert groups is None

        return web.Response(text='test')

    acl.setup(app, _none_groups_callback)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_acl_permissions(app, client):
    async def handler_test(request):
        context = [(Permission.Allow, 'group0', ('test0',)),
                   (Permission.Deny, 'group1', ('test1',)),
                   (Permission.Allow, Group.Everyone, ('test1',))]

        assert (await acl.get_permitted(request, 'test0', context)) is True
        assert (await acl.get_permitted(request, 'test1', context)) is False

        return web.Response(text='test')

    acl.setup(app, _groups_callback)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_permission_order(app, client):
    context = [(Permission.Allow, Group.Everyone, ('test0',)),
               (Permission.Deny, 'group1', ('test1',)),
               (Permission.Allow, Group.Everyone, ('test1',))]

    async def handler_test0(request):
        assert (await acl.get_permitted(request, 'test0', context)) is True
        assert (await acl.get_permitted(request, 'test1', context)) is False

        return web.Response(text='test0')

    async def handler_test1(request):
        assert (await acl.get_permitted(request, 'test0', context)) is True
        assert (await acl.get_permitted(request, 'test1', context)) is True

        return web.Response(text='test1')

    acl.setup(app, _auth_groups_callback)
    app.router.add_get('/test0', handler_test0)
    app.router.add_get('/test1', handler_test1)

    cli = await client(app)

    await assert_response(cli.get('/test1'), 'test1')
    await assert_response(cli.get('/remember'), 'remember')
    await assert_response(cli.get('/test0'), 'test0')


async def test_acl_required_decorator(loop, app, client):
    context = [(Permission.Deny, 'group0', ('test0',)),
               (Permission.Allow, 'group0', ('test1',)),
               (Permission.Allow, 'group1', ('test0', 'test1'))]

    class GroupsCallback:
        def __init__(self, group=None):
            self.group = group

        async def groups(self):
            if self.group is None:
                return None

            return (self.group, )

        def __call__(self, user_id):
            return self.groups()

    @acl.acl_required('test0', context)
    async def handler_test(request):
        return web.Response(text='test')

    groups_callback = GroupsCallback()
    acl.setup(app, groups_callback)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    response = await cli.get('/test')
    assert response.status == 403

    groups_callback.group = 'group0'
    response = await cli.get('/test')
    assert response.status == 403

    groups_callback.group = 'group1'
    response = await cli.get('/test')
    await assert_response(cli.get('/test'), 'test')


async def test_acl_not_matching_acl_group(app, client):
    async def handler_test(request):
        context = [(Permission.Allow, 'group2', ('test0')),
                   (Permission.Allow, 'group3', ('test0', 'test1'))]

        assert (await acl.get_permitted(request, 'test0', context)) is False
        assert (await acl.get_permitted(request, 'test1', context)) is False

        return web.Response(text='test')

    acl.setup(app, _groups_callback)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_acl_permission_deny_for_user_id_equals_to_group_name(app,
                                                                    client):
    context = [(Permission.Allow, 'group0', ('test0',)),
               (Permission.Deny, 'group1', ('test0',))]

    async def _groups1_callback(user_id):
        return ('group1', )

    async def handler_test(request):
        assert (await acl.get_permitted(request, 'test0', context)) is False

        return web.Response(text='test')

    async def handler_remember_group0(request):
        await auth.remember(request, 'group0')
        return web.Response(text='remember_group0')

    acl.setup(app, _groups1_callback)
    app.router.add_get('/test', handler_test)
    app.router.add_get('/remember_group0', handler_remember_group0)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')
    await assert_response(cli.get('/remember_group0'), 'remember_group0')
    await assert_response(cli.get('/test'), 'test')
