"""ACL abstract classes."""
import abc


class AbstractACLGroupsCallback(abc.ABC):
    """Abstract base class for acl_groups_callback callabel.

    User should create class deriving from this one, override acl_groups
    method and register object of that class with setup function as
    acl_groups_callback.

    Usage example:

    .. code-block:: python

        class ACLGroupsCallback(AbstractACLGroupsCallback):

            def __init__(self, cache):
                # store some kind of cache
                self.cache = cache

            async def acl_groups(self, user_id):
                # implement logic to return user's groups.
                user = await self.cache.get(user_id)
                return user.groups()


        def init(loop):
            app = web.Application(loop=loop)
            ...
            cache = ...
            acl_groups_callback = ACLGroupsCallback(cache)

            acl.setup(app, acl_groups_callback)
            ...

    """

    @abc.abstractmethod
    async def acl_groups(self, user_id):
        """Return ACL groups for given user identity.

        Note that the ACL groups returned by this method will be modified by
        the acl_middleware to also include the Group.Everyone group (if the
        value returned is not None), and also the Group.AuthenticatedUser
        if the user_id is not None.

        Args:
            user_id: User identity (as returned from the auth.get_auth
                function). Note that the user_id passed may be None if no
                authenticated user exists.

        Returns:
            A sequence of permitted ACL groups. This can be a empty tuple to
            represent no explicit permissions, or None to explicitly forbid
            this particular user_id.
        """
        pass  # pragma: no cover

    def __call__(self, user_id):
        return self.acl_groups(user_id)
