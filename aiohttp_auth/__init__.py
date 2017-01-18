from .auth import auth_middleware
from .autz import autz_middleware
from .acl import acl_middleware
from . import auth, acl, autz


def setup(app, auth_policy, autz_policy):
    """Setup auth and autz middleware in aiohttp fashion.

    Args:
        app: aiohttp Application object.
        auth_policy: An authentication policy with a base class of
            AbstractAuthentication.
        autz_policy: An authorization policy with a base class of
            AbstractAutzPolicy
    """
    auth.setup(app, auth_policy)
    autz.setup(app, autz_policy)
