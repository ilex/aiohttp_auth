"""ACL middleware."""
import itertools
from ..auth import get_auth
from ..permissions import Permission, Group


GROUPS_KEY = 'aiohttp_auth.acl.callback'


def acl_middleware(callback):
    """Return ACL middleware factory.

    The middleware is for use by the aiohttp application object.

    Args:
        callback: This is a callable which takes a user_id (as returned from
            the auth.get_auth function), and expects a sequence of permitted
            ACL groups to be returned. This can be a empty tuple to represent
            no explicit permissions, or None to explicitly forbid this
            particular user_id. Note that the user_id passed may be None if no
            authenticated user exists.

    Returns:
        A aiohttp middleware factory.
    """
    async def _acl_middleware_factory(app, handler):

        async def _middleware_handler(request):
            # Save the policy in the request
            request[GROUPS_KEY] = callback

            # Call the next handler in the chain
            return await handler(request)

        return _middleware_handler

    return _acl_middleware_factory


async def get_user_groups(request):
    """Return the groups that the user in this request has access to.

    This function gets the user id from the auth.get_auth function, and passes
    it to the ACL callback function to get the groups.

    Args:
        request: aiohttp Request object.

    Returns:
        If the ACL callback function returns None, this function returns None.
        Otherwise this function returns the sequence of group permissions
        provided by the callback, plus the Everyone group. If user_id is not
        None, the AuthnticatedUser group is added to the groups returned
        by the function.

    Raises:
        RuntimeError: If the ACL middleware is not installed.
    """
    acl_callback = request.get(GROUPS_KEY)
    if acl_callback is None:
        raise RuntimeError('acl_middleware not installed')

    user_id = await get_auth(request)
    groups = await acl_callback(user_id)

    return extend_user_groups(user_id, groups)


def extend_user_groups(user_id, groups):
    """Extend user groups with specific Groups.

    Args:
        user_id: User identity from get_auth.
        groups: User groups.

    Returns:
        If groups is None, this function returns None.
        Otherwise this function extends groups with the Everyone group.
        If user_id is not None, the AuthnticatedUser group is added to the
        groups returned by the function.
    """
    if groups is None:
        return None

    user_groups = (Group.AuthenticatedUser, ) if user_id is not None else ()

    return set(itertools.chain(groups, (Group.Everyone,), user_groups))


async def get_permitted(request, permission, context):
    """Check permission for the given request with the given context.

    Return True if the one of the groups in the request has the requested
    permission.

    The function takes a request, a permission to check for and a context. A
    context is a sequence of ACL tuples which consist of a Allow/Deny action,
    a group, and a sequence of permissions for that ACL group. For example:

    .. code-block:: python

        context = [(Permission.Allow, 'view_group', ('view',)),
                   (Permission.Allow, 'edit_group', ('view', 'edit')),]

    ACL tuple sequences are checked in order, with the first tuple that matches
    the group the user is a member of, and includes the permission passed to
    the function, to be the matching ACL group. If no ACL group is found, the
    function returns False.

    Groups and permissions need only be immutable objects, so can be strings,
    numbers, enumerations, or other immutable objects.

    Args:
        request: aiohttp Request object.
        permission: The specific permission requested.
        context: A sequence of ACL tuples.

    Returns:
        The function gets the groups by calling get_user_groups() and returns
        true if the groups are Allowed the requested permission, false
        otherwise.

    Raises:
        RuntimeError: If the ACL middleware is not installed.
    """
    groups = await get_user_groups(request)
    return get_groups_permitted(groups, permission, context)


def get_groups_permitted(groups, permission, context):
    """Check if one of the groups has the requested permission.

    Args:
        groups: A set of ACL groups.
        permission: The specific permission requested.
        context: A sequence of ACL tuples.

    Returns:
        True if the groups are Allowed the requested permission, False
        otherwise.
    """
    if groups is None:
        return False

    for action, group, permissions in context:
        if group in groups:
            if permission in permissions:
                return action == Permission.Allow

    return False


def setup(app, groups_callback):
    """Setup middleware in aiohttp fashion.

    Args:
        app: aiohttp Application object.
        groups_callback: This is a callable which takes a user_id (as returned
            from the auth.get_auth function), and expects a sequence of
            permitted ACL groups to be returned. This can be a empty tuple to
            represent no explicit permissions, or None to explicitly forbid
            this particular user_id. Note that the user_id passed may be None
            if no authenticated user exists.
    """
    app.middlewares.append(acl_middleware(groups_callback))
