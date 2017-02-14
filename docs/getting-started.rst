Getting Started
===============

A simple example how to use authentication and authorization middleware
with an aiohttp application.

.. code-block:: python

    import asyncio

    from aiohttp import web
    from aiohttp_auth import auth, autz, Permission
    from aiohttp_auth.auth import auth_required 
    from aiohttp_auth.autz import autz_required
    from aiohttp_auth.autz.policy import acl

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
               (Permission.Allow, 'staff', {'view', 'edit', 'admin_view'})]

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
                return None 

            return user['groups']



    async def login(request):
        post = await request.post()
        user_identity = post.get('username', None)
        password = post.get('password', None)
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

    async def home(request):
        text = 'Home page.'
        # check if current user is permitted with 'admin_view' permission
        if await autz.permit(request, 'admin_view'):
            text += ' Go to <a href="/admin">admin</a>'
        return web.Response(text=text)

    @autz_required('view')
    async def view(request):
        return web.Response(text='View Page')
            

    def init(loop):
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

        app.router.add_post('/login', login)
        app.router.add_get('/logout', logout)
        app.router.add_get('/admin', admin)
        app.router.add_get('/view', view)
        app.router.add_get('/', home)

        web.run_app(app)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
