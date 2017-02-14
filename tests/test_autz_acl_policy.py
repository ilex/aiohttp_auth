import pytest
import aiohttp_session
from aiohttp import web
from aiohttp_auth import auth, autz
from aiohttp_auth.autz import autz_required
from aiohttp_auth.autz.policy import acl
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


class ACLAutzPolicy(acl.AbstractACLAutzPolicy):
    """Policy that always returns the same two groups."""
    async def acl_groups(self, user_identity):
        return ('group0', 'group1')


class AuthACLAutzPolicy(acl.AbstractACLAutzPolicy):
    """Policy that always returns the same two groups."""
    async def acl_groups(self, user_identity):
        if user_identity:
            return ('group0', 'group1')

        return ()


class NoneACLAutzPolicy(acl.AbstractACLAutzPolicy):
    """Policy that always returns None."""
    async def acl_groups(self, user_id):
        return None


async def test_autz_middleware_setup(app):
    autz_policy = ACLAutzPolicy([])
    autz.setup(app, autz_policy)

    middleware = autz.autz_middleware(autz_policy)

    assert app.middlewares[-1].__name__ == middleware.__name__


async def test_no_middleware_installed(app, client):
    async def handler_test(request):
        with pytest.raises(RuntimeError) as exc_info:
            await autz.permit(request, 'edit', [])

        assert str(exc_info.value) == 'autz_middleware not installed.'

        return web.Response(text='test')

    app.router.add_get('/test', handler_test)
    cli = await client(app)

    await assert_response(cli.get('/remember'), 'remember')

    await assert_response(cli.get('/test'), 'test')


async def test_correct_groups_returned_for_authenticated_user():
    policy = ACLAutzPolicy([])
    groups = await policy.acl_groups('some_user')
    groups = await policy.context.extended_user_groups('some_user', groups)

    assert 'group0' in groups
    assert 'group1' in groups
    assert 'some_user' not in groups
    assert Group.Everyone in groups
    assert Group.AuthenticatedUser in groups


async def test_correct_groups_returned_for_unauthenticated_user():
    policy = ACLAutzPolicy([])
    groups = await policy.acl_groups(None)
    groups = await policy.context.extended_user_groups(None, groups)

    assert 'group0' in groups
    assert 'group1' in groups
    assert 'some_user' not in groups
    assert Group.Everyone in groups
    assert Group.AuthenticatedUser not in groups


async def test_no_groups_if_none_returned_from_acl_groups():
    policy = NoneACLAutzPolicy([])
    groups = await policy.acl_groups(None)
    groups = await policy.context.extended_user_groups(None, groups)

    assert groups is None


async def test_autz_acl_policy_permit_with_local_context():
    context = [(Permission.Allow, 'group0', ('test0',)),
               (Permission.Deny, 'group1', ('test1',)),
               (Permission.Allow, Group.Everyone, ('test1',))]

    policy = ACLAutzPolicy(None)

    assert (await policy.permit(None, 'test0', context)) is True
    assert (await policy.permit(None, 'test1', context)) is False


async def test_autz_acl_policy_permit_with_global_context():
    context = [(Permission.Allow, 'group0', ('test0',)),
               (Permission.Deny, 'group1', ('test1',)),
               (Permission.Allow, Group.Everyone, ('test1',))]

    policy = ACLAutzPolicy(context)

    assert (await policy.permit(None, 'test0')) is True
    assert (await policy.permit(None, 'test1')) is False


async def test_autz_permit_with_acl_policy_local_context(app, client):
    context = [(Permission.Allow, 'group0', ('test0',)),
               (Permission.Deny, 'group1', ('test1',)),
               (Permission.Allow, Group.Everyone, ('test1',))]

    async def handler_test(request):
        assert (await autz.permit(request, 'test0', context)) is True
        assert (await autz.permit(request, 'test1', context)) is False

        return web.Response(text='test')

    policy = ACLAutzPolicy(None)
    autz.setup(app, policy)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_autz_permit_with_acl_policy_global_context(app, client):
    context = [(Permission.Allow, 'group0', ('test0',)),
               (Permission.Deny, 'group1', ('test1',)),
               (Permission.Allow, Group.Everyone, ('test1',))]

    async def handler_test(request):
        assert (await autz.permit(request, 'test0')) is True
        assert (await autz.permit(request, 'test1')) is False

        return web.Response(text='test')

    policy = ACLAutzPolicy(context)
    autz.setup(app, policy)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_autz_permit_acl_policy_replace_global_context_with_local(
        app, client):
    context = [(Permission.Deny, 'group1', ('test1', ))]

    async def handler_test(request):
        local_context = [(Permission.Allow, 'group1', ('test1', ))]

        # with global context
        assert (await autz.permit(request, 'test1')) is False
        # with local context
        assert (await autz.permit(request, 'test1', local_context)) is True

        return web.Response(text='test')

    policy = ACLAutzPolicy(context)
    autz.setup(app, policy)
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_autz_acl_policy_permission_order(app, client):
    context = [(Permission.Allow, Group.Everyone, ('test0',)),
               (Permission.Deny, 'group1', ('test1',)),
               (Permission.Allow, Group.Everyone, ('test1',))]

    async def handler_test0(request):
        assert (await autz.permit(request, 'test0', context)) is True
        assert (await autz.permit(request, 'test0')) is True
        assert (await autz.permit(request, 'test1', context)) is False
        assert (await autz.permit(request, 'test1')) is False

        return web.Response(text='test0')

    async def handler_test1(request):
        assert (await autz.permit(request, 'test0', context)) is True
        assert (await autz.permit(request, 'test0')) is True
        assert (await autz.permit(request, 'test1', context)) is True
        assert (await autz.permit(request, 'test1')) is True

        return web.Response(text='test1')

    autz.setup(app, AuthACLAutzPolicy(context))
    app.router.add_get('/test0', handler_test0)
    app.router.add_get('/test1', handler_test1)

    cli = await client(app)

    await assert_response(cli.get('/test1'), 'test1')
    await assert_response(cli.get('/remember'), 'remember')
    await assert_response(cli.get('/test0'), 'test0')


async def test_autz_required_decorator_with_acl_policy(loop, app, client):
    context = [(Permission.Deny, 'group0', ('test0',)),
               (Permission.Allow, 'group0', ('test1',)),
               (Permission.Allow, 'group1', ('test0', 'test1'))]

    class CustomACLAutzPolicy(acl.AbstractACLAutzPolicy):
        def __init__(self, group=None, context=None):
            super().__init__(context)
            self.group = group

        async def acl_groups(self, user_identity):
            if self.group is None:
                return None

            return (self.group, )

    @autz_required('test0', context)
    async def handler_test(request):
        return web.Response(text='test')

    @autz_required('test0')
    async def handler_test_global(request):
        return web.Response(text='test_global')

    policy = CustomACLAutzPolicy(context=context)
    autz.setup(app, policy)
    app.router.add_get('/test', handler_test)
    app.router.add_get('/test_global', handler_test_global)

    cli = await client(app)

    response = await cli.get('/test')
    assert response.status == 403
    response = await cli.get('/test_global')
    assert response.status == 403

    policy.group = 'group0'
    response = await cli.get('/test')
    assert response.status == 403
    response = await cli.get('/test_global')
    assert response.status == 403

    policy.group = 'group1'
    await assert_response(cli.get('/test'), 'test')
    await assert_response(cli.get('/test_global'), 'test_global')


async def test_autz_acl_not_matching_acl_group(app, client):
    context = [(Permission.Allow, 'group2', ('test0')),
               (Permission.Allow, 'group3', ('test0', 'test1'))]

    async def handler_test(request):
        assert (await autz.permit(request, 'test0', context)) is False
        assert (await autz.permit(request, 'test0')) is False
        assert (await autz.permit(request, 'test1', context)) is False
        assert (await autz.permit(request, 'test1')) is False

        return web.Response(text='test')

    autz.setup(app, ACLAutzPolicy(context))
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_autz_acl_no_context_raises_error(app, client):
    async def handler_test(request):
        with pytest.raises(RuntimeError) as exc_info:
            await autz.permit(request, 'test0')

        assert str(exc_info.value) == ('Context should be specified globally '
                                       'through acl autz policy or passed as '
                                       'a parameter of permit function or '
                                       'autz_required decorator.')

        return web.Response(text='test')

    autz.setup(app, ACLAutzPolicy())
    app.router.add_get('/test', handler_test)

    cli = await client(app)

    await assert_response(cli.get('/test'), 'test')


async def test_autz_acl_naive_context():
    acl_context = [(Permission.Allow, 'group2', ('test0'))]

    context = acl.NaiveACLContext(acl_context)

    assert context._context == acl_context


async def test_autz_acl_context():
    acl_context = [(Permission.Allow, 'group0', ('test0'))]

    context = acl.ACLContext(acl_context)

    assert context._context != acl_context
    assert isinstance(context._context, tuple)
    assert isinstance(context._context[0][2], set)


@pytest.mark.parametrize('context_class', (acl.NaiveACLContext,
                                           acl.ACLContext))
async def test_autz_acl_context_permit(context_class):
    acl_context = [(Permission.Allow, 'group0', ('test0', 'test2')),
                   (Permission.Deny, 'group1', ('test1',)),
                   (Permission.Allow, 'group0', ('test1', 'test0')),
                   (Permission.Allow, 'group1', ('test1', 'test0'))]

    context = context_class(acl_context)

    assert (await context.permit(None, {'group0', }, 'test0')) is True
    assert (await context.permit(None, {'group0', }, 'test1')) is True
    assert (await context.permit(None, {'group0', }, 'test2')) is True
    assert (await context.permit(None, {'group0', }, 'test3')) is False

    assert (await context.permit(None, {'group1', }, 'test0')) is True
    assert (await context.permit(None, {'group1', }, 'test1')) is False
    assert (await context.permit(None, {'group1', }, 'test2')) is False
    assert (await context.permit(None, {'group1', }, 'test3')) is False

    assert (await context.permit(None, {'group3', }, 'test1')) is False
    assert (await context.permit(None, {'group3', }, 'test2')) is False
    assert (await context.permit(None, {'group3', }, 'test3')) is False
    assert (await context.permit(None, {'group3', }, 'test4')) is False
