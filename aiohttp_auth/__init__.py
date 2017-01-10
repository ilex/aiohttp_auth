from .auth import auth_middleware
from .acl import acl_middleware
from . import auth, acl


def setup(app, auth_policy, acl_groups_callback):
    """Setup auth and acl middleware in aiohttp fashion.

    Args:
        app: aiohttp Application object.
        auth_policy: An authentication policy with a base class of
            AbstractAuthentication.
        acl_groups_callback: This is a callable which takes a user_id (as
            returned from the auth.get_auth function), and expects a sequence
            of permitted ACL groups to be returned. This can be a empty tuple
            to represent no explicit permissions, or None to explicitly forbid
            this particular user_id. Note that the user_id passed may be None
            if no authenticated user exists.
    """
    auth.setup(app, auth_policy)
    acl.setup(app, acl_groups_callback)
