"""ACL authorization policy.

This module introduces ``AbstractACLAutzPolicy`` - an abstract base class to
create ACL authorization policy class. The subclass should define how to
retrieve user's groups.
"""
import abc
from ...acl.acl import extend_user_groups, get_groups_permitted
from ..abc import AbstractAutzPolicy


class AbstractACLAutzPolicy(AbstractAutzPolicy):
    """Abstract base class for ACL authorization policy.

    As the library does not know how to get groups for user and it is always
    up to application, it provides abstract authorization ACL policy
    class. Subclass should implement ``acl_groups`` method to use it with
    ``autz_middleware``.

    Note that an ACL context can be specified globally while initializing
    policy or locally through ``autz.permit`` function's parameter. A local
    context will always override a global one while checking permissions.
    If there is no local context and global context is not set then the
    ``permit`` method will raise a ``RuntimeError``.

    A context is  a sequence of ACL tuples which consist of an
    ``Allow``/``Deny`` action, a group, and a set of permissions for that ACL
    group. For example:

    .. code-block:: python

        context = [(Permission.Allow, 'view_group', {'view', }),
                   (Permission.Allow, 'edit_group', {'view', 'edit'}),]

    ACL tuple sequences are checked in order, with the first tuple that
    matches the group the user is a member of, and includes the permission
    passed to the function, to be the matching ACL group. If no ACL group is
    found, the ``permit`` method returns ``False``.

    Groups and permissions need only be immutable objects, so can be strings,
    numbers, enumerations, or other immutable objects.

    .. note:: Groups that are returned by ``acl_groups`` (if they are not
        ``None``) will then be extended internally with ``Group.Everyone`` and
        ``Group.AuthenticatedUser``.

    Usage example:

    .. code-block:: python

        from aiohttp import web
        from aiohttp_auth import autz
        from aiohttp_auth.autz import autz_required
        from aiohttp_auth.autz.policy import acl
        from aiohttp_auth.permissions import Permission


        class ACLAutzPolicy(acl.AbstractACLAutzPolicy):
            def __init__(self, users, context=None):
                super().__init__(context)

                # we will retrieve groups using some kind of users dict
                # here you can use db or cache or any other needed data
                self.users = users

            async def acl_groups(self, user_identity):
                # implement application specific logic here
                user = self.users.get(user_identity, None)
                if user is None:
                    return None

                return user['groups']


        def init(loop):
            app = web.Application(loop=loop)
            ...
            # here you need to initialize aiohttp_auth.auth middleware
            ...
            users = ...
            # Create application global context.
            # It can be overridden in autz.permit fucntion or in
            # autz_required decorator using local context explicitly.
            context = [(Permission.Allow, 'view_group', {'view', }),
                       (Permission.Allow, 'edit_group', {'view', 'edit'})]
            autz.setup(app, ACLAutzPolicy(users, context))


        # authorization using autz decorator applying to app request handler
        @autz_required('view')
        async def handler_view(request):
            # authorization using permit
            if await autz.permit(request, 'edit'):
                pass

    """

    def __init__(self, context=None):
        """Initialize ACL authorization policy.

        Args:
            context: global ACL context, default to ``None``. Should be a list
                of ACL rules.
        """
        self.context = context

    @abc.abstractmethod
    async def acl_groups(self, user_identity):
        """Return ACL groups for given user identity.

        Subclass should implement this method to return a sequence of
        groups for given ``user_identity``.

        Args:
            user_identity: User identity returned by ``auth.get_auth``.

        Returns:
            Sequence of ACL groups for the user identity (could be empty to
            give a chance to ``Group.Everyone`` and
            ``Group.AuthenticatedUser``) or ``None`` (``permit`` will always
            return ``False``).
        """
        pass  # pragma: no cover

    async def permit(self, user_identity, permission, context=None):
        """Check if user is allowed for given permission with given context.

        Args:
            user_identity: Identity of the user returned by
                ``aiohttp_auth.auth.get_auth`` function
            permission: The specific permission requested.
            context: A context provided for checking permissions. Could be
                optional if a global context is specified through policy
                initialization.

        Returns:
            ``True`` if permission is allowed, ``False`` otherwise.

        Raises:
            RuntimeError: If there is neither global context nor local one.
        """
        if context is None:
            # try global context
            context = self.context

        if context is None:
            raise RuntimeError('Context should be specified globally through '
                               'acl autz policy or passed as a parameter of '
                               'permit function or autz_required decorator.')

        groups = extend_user_groups(user_identity,
                                    await self.acl_groups(user_identity))
        return get_groups_permitted(groups, permission, context)
