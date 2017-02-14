aiohttp_auth_autz
=================

.. image:: https://travis-ci.org/ilex/aiohttp_auth_autz.svg?branch=master
    :target: https://travis-ci.org/ilex/aiohttp_auth_autz

.. image:: https://readthedocs.org/projects/aiohttp-auth-autz/badge/?version=latest
    :target: http://aiohttp-auth-autz.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

This library provides authorization and authentication middleware plugins for
aiohttp servers.

These plugins are designed to be lightweight, simple, and extensible, allowing
the library to be reused regardless of the backend authentication mechanism.
This provides a familiar framework across projects.

There are three middleware plugins provided by the library. The ``auth_middleware``
plugin provides a simple system for authenticating a users credentials, and
ensuring that the user is who they say they are.

The ``autz_middleware`` plugin provides a generic way of authorization using 
different authorization policies. There is the ACL authorization policy as a
part of the plugin.

The ``acl_middleware`` plugin provides a simple access control list authorization
mechanism, where users are provided access to different view handlers depending
on what groups the user is a member of. It is recomended to use ``autz_middleware``
with ACL policy instead of this middleware.

This is a fork of `aiohttp_auth <https://github.com/gnarlychicken/aiohttp_auth>`_
library that fixes some bugs and security issues and also introduces a generic 
authorization ``autz`` middleware with built in ACL authorization policy.


Documentation
-------------

http://aiohttp-auth-autz.readthedocs.io/


Install
-------

Install ``aiohttp_auth_autz`` using ``pip``::

    $ pip install aiohttp_auth_autz


Getting Started
---------------

.. code-block:: python

    import asyncio

    from os import urandom

    import aiohttp_auth

    from aiohttp import web
    from aiohttp_auth import auth, autz
    from aiohttp_auth.auth import auth_required
    from aiohttp_auth.autz import autz_required
    from aiohttp_auth.autz.policy import acl
    from aiohttp_auth.permissions import Permission, Group

    db = {
        'bob': {
            'password': 'bob_password',
            'groups': ['guest', 'staff']
        },
        'alice': {
            'password': 'alice_password',
            'groups': ['guest']
        }
    }

    # global ACL context
    context = [(Permission.Allow, 'guest', {'view', }),
            (Permission.Deny, 'guest', {'edit', }),
            (Permission.Allow, 'staff', {'view', 'edit', 'admin_view'}),
            (Permission.Allow, Group.Everyone, {'view_home', })]


    # create an ACL authorization policy class
    class ACLAutzPolicy(acl.AbstractACLAutzPolicy):
        """The concrete ACL authorization policy."""

        def __init__(self, db, context=None):
            # do not forget to call parent __init__
            super().__init__(context)

            self.db = db

        async def acl_groups(self, user_identity):
            """Return acl groups for given user identity.

            This method should return a set of groups for given user_identity.

            Args:
                user_identity: User identity returned by auth.get_auth.

            Returns:
                Set of acl groups for the user identity.
            """
            # implement application specific logic here
            user = self.db.get(user_identity, None)
            if user is None:
                # return empty set of groups for not authenticated users
                # middleware will fill it with Group.Everyone
                return set()

            return user['groups']


    async def login(request):
        # http://127.0.0.1:8080/login?username=bob&password=bob_password
        user_identity = request.GET.get('username', None)
        password = request.GET.get('password', None)
        if user_identity in db and password == db[user_identity]['password']:
            # remember user identity
            await auth.remember(request, user_identity)
            return web.Response(text='Ok')

        raise web.HTTPUnauthorized()


    # only authenticated users can logout
    # if user is not authenticated auth_required decorator
    # will raise a web.HTTPUnauthorized
    @auth_required
    async def logout(request):
        # forget user identity
        await auth.forget(request)
        return web.Response(text='Ok')


    # user should have a group with 'admin_view' permission allowed
    # if he does not autz_required will raise a web.HTTPForbidden
    @autz_required('admin_view')
    async def admin(request):
        return web.Response(text='Admin Page')


    @autz_required('view_home')
    async def home(request):
        text = 'Home page.'
        # check if current user is permitted with 'admin_view' permission
        if await autz.permit(request, 'admin_view'):
            text += ' Admin page: http://127.0.0.1:8080/admin'
        # get current user identity
        user_identity = await auth.get_auth(request)
        if user_identity is not None:
            # user is authenticated
            text += ' Logout: http://127.0.0.1:8080/logout'
        return web.Response(text=text)


    @autz_required('view')
    async def view(request):
        return web.Response(text='View Page')


    def init_app(loop):
        app = web.Application(loop=loop)

        # Create an auth ticket mechanism that expires after 1 minute (60
        # seconds), and has a randomly generated secret. Also includes the
        # optional inclusion of the users IP address in the hash
        auth_policy = auth.CookieTktAuthentication(urandom(32), 60,
                                                include_ip=True)

        # Create an ACL authorization policy
        autz_policy = ACLAutzPolicy(db, context)

        # setup middlewares in aiohttp fashion
        aiohttp_auth.setup(app, auth_policy, autz_policy)

        app.router.add_get('/', home)
        app.router.add_get('/login', login)
        app.router.add_get('/logout', logout)
        app.router.add_get('/admin', admin)
        app.router.add_get('/view', view)

        return app


    loop = asyncio.get_event_loop()
    app = init_app(loop)

    web.run_app(app, host='127.0.0.1')


License
-------

The library is licensed under a MIT license.
