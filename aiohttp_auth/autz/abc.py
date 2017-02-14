"""Abstract authorization classes."""
import abc


class AbstractAutzPolicy(abc.ABC):
    """Abstact base class for authentication policies.

    Each policy should be inherited from this class and implement
    ``permit`` method. That is all needed to use such policy with
    ``autz_middleware``.
    """

    @abc.abstractmethod
    async def permit(self, user_identity, permission, context):
        """Check if user has permission accoding to context.

        Args:
            user_identity: User identity returned from ``auth.get_auth``.
            permission: Permission method checks for.
            context: Context which is used to determine permit of permission.

        Returns:
            ``True`` if permission is allowed and ``False`` otherwise.
        """
        pass  # pragma: no cover
