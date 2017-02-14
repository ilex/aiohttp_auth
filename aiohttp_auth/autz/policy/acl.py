"""ACL authorization policy.

This module introduces:
    ``AbstractACLAutzPolicy``: Abstract base class to create ACL authorization
        policy class. The subclass should define how to retrieve users
        groups.
    ``AbstractACLContext``: Abstract base class for ACL context containers.
        Context container defines a representation of ACL data structure,
        a storage method and how to process ACL context and groups
        to authorize user with permissions.
    ``NaiveACLContext``: ACL context container which is initialized with list
        of ACL tuples and stores them as they are. The implementation
        of permit process is the same as used by ``acl_middleware``.
    ``ACLContext``: The same as ``NaiveACLContext`` but makes some
        transformation of incoming ACL tuples. This may helps with a
        perfomance of the permit process.
"""
import abc
from ...acl.acl import extend_user_groups, get_groups_permitted
from ..abc import AbstractAutzPolicy


class AbstractACLContext(abc.ABC):
    """Abstract base class for all ACL context classes.

    Policy uses context classes to wrap sequence of ACL groups
    permissions. This allows to implement different type of structures
    to store permissions and/or to proccess them in a specific way.

    The only required method to implement in subclasses is permit.
    """

    @abc.abstractmethod
    async def permit(self, user_identity, groups, permission):
        """Check if permission is allowed for groups.

        Args:
            user_identity: Identity of the user returned by ``auth.get_auth``.
            groups: Some set of groups for which permission is checked for.
            permission: Permission that is checked.

        Returns:
            ``True`` if permission is allowed, ``False`` otherwise.
        """
        pass  # pragma: no cover


class NaiveACLContext(AbstractACLContext):
    """Naive implementation of ACL context.

    This class does not make any transformation of the ACL groups
    permissions which are passed through constructor but stores
    them as they are.

    It uses the default permit strategy from ``acl_middleware``.
    """

    def __init__(self, context):
        """Constructor.

        Args:
            context: is a sequence of ACL tuples which consist of
                an ``Allow``/``Deny`` action, a group, and a sequence of
                permissions for that ACL group. For example:

                .. code-block:: python

                    context = [(Permission.Allow, 'view_group', ('view',)),
                               (Permission.Allow, 'edit_group', ('view',
                                                                 'edit')),]
        """
        self._context = context

    async def extended_user_groups(self, user_identity, groups):
        """Extend user groups with ACL specific groups.

        See ``acl_middleware`` for more information.
        """
        return extend_user_groups(user_identity, groups)

    async def permit(self, user_identity, groups, permission):
        """Permit accoding to ``alc_middleware`` strategy.

        Args:
            user_identity: Identity of the user returned by ``auth.get_auth``.
            groups: Set of user groups.
            permission: Permission that is checked.

        Returns:
            ``True`` if permission is allowed, ``False`` otherwise.
        """
        groups = await self.extended_user_groups(user_identity, groups)
        return get_groups_permitted(groups, permission, self._context)


class ACLContext(NaiveACLContext):
    """ACL context implementation.

    This acl context implementation works in the same way as NaiveACLContext
    but acl groups permissions context is transformed to meet best perfomance
    using permit strategy from acl_middleware.
    """

    def __init__(self, context):
        """Constructor.

        Args:
            context: The same as for NaiveACLContext.
        """
        super().__init__(tuple((action, group, set(permissions))
                               for action, group, permissions in context))


class AbstractACLAutzPolicy(AbstractAutzPolicy):
    """Abstract base class for ACL authorization policy.

    As the library does not know how to get groups for user and it is always
    up to application, it provides abstract authorization ACL policy
    class. Subclass should implement ``acl_groups`` method to use it with
    ``autz_middleware``.

    Note that an acl context can be specified globally while initializing
    policy or locally through ``autz.permit`` function's parameter. A local
    context will always override a global one while checking permissions.
    If there is no local context and global context is not set then the
    ``permit`` method will raise a ``RuntimeError``.

    A context is an instance of ``AbstractACLContext`` subclass or a sequence
    of ACL tuples which consist of a ``Allow``/``Deny`` action, a group, and a
    sequence of permissions for that ACL group.
    For example:

    .. code-block:: python

        context = [(Permission.Allow, 'view_group', ('view',)),
                   (Permission.Allow, 'edit_group', ('view', 'edit')),]

    ACL tuple sequences are checked in order, with the first tuple that
    matches the group the user is a member of, and includes the permission
    passed to the function, to be the matching ACL group. If no ACL group is
    found, the permit method returns False.

    Groups and permissions need only be immutable objects, so can be strings,
    numbers, enumerations, or other immutable objects.

    Note that custom implementation of ``AbstractACLContext`` can be used to
    change the context form and the way it is processed.

    Usage example:

    .. code-block:: python

        from aiohttp import web
        from aiohttp_auth import autz, Permission
        from aiohttp_auth.autz import autz_required
        from aiohttp_auth.autz.policy import acl


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


        # authorization using autz decorator applying to app handler
        @autz_required('view')
        async def handler_view(request):
            # authorization using permit
            if await autz.permit(request, 'edit'):
                pass

    """

    def __init__(self, context=None):
        """Initialize ACL authorization policy.

        Args:
            context: global ACL context, default to ``None``. Could be an
                ``AbstractACLContext`` subclass instance or raw list of ACL
                rules.
        """
        if context is None or isinstance(context, AbstractACLContext):
            self.context = context
        else:
            self.context = ACLContext(context)

    @abc.abstractmethod
    async def acl_groups(self, user_identity):
        """Return ACL groups for given user identity.

        Subclass should implement this method to return a set of
        groups for given ``user_identity``.

        Args:
            user_identity: User identity returned by ``auth.get_auth``.

        Returns:
            Set of ACL groups for the user identity.
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

        if not isinstance(context, AbstractACLContext):
            # if there is a raw acl context data
            # we use NaiveACLContext wrapper which just
            # stores it internally and makes no transformations
            # which is important as of the perfomance point.
            context = NaiveACLContext(context)

        groups = await self.acl_groups(user_identity)
        return await context.permit(user_identity, groups, permission)
