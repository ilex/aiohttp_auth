Changelog
=========

0.2.0 (2017-02-14)
------------------

- ``acl`` middleware:

  - Add ``setup`` function for ``acl`` middleware to install it in aiohttp fashion.

  - Fix bug in ``acl_required`` decorator.

  - Fix a possible security issue with ``acl`` groups. The issue is follow: the default behavior is
    to add ``user_id`` to groups for authenticated users by the acl middleware, but if 
    ``user_id`` is equal to some of acl groups that user suddenly has the permissions he is not 
    allowed for. So to avoid this kind of issue ``user_id`` is not added to groups any more. 

  - Introduce ``AbstractACLGroupsCallback`` class in ``acl`` middleware to make it possible easily create 
    callable object by inheriting from the abstract class and implementing ``acl_groups`` method. It
    can be useful to store additional information (such database connection etc.) within such class.
    An instance of this subclass can be used in place of ``acl_groups_callback`` parameter.

- ``auth`` middleware:

  - Add ``setup`` function for ``auth`` middleware to install it in aiohttp fashion.

  - ``auth.auth_required`` raised now a ``web.HTTPUnauthorized`` instead of a ``web.HTTPForbidden``.

- Introduce generic authorization middleware ``autz`` that performs authorization through the same
  interface (``autz.permit`` coroutine and ``autz_required`` decorator) but using different policies. 
  Middleware has the ACL authorization as the built in policy which works in the same way as ``acl``
  middleware. Users are free to add their own custom policies or to modify ACL one.

- Add global ``aiohttp_auth.setup`` function to install ``auth`` and ``autz`` middlewares at once 
  in aiohttp fashion.

- Add docs.

- Rewrite tests using ``pytest`` and ``pytest-aiohttp``.
