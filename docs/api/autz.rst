Authorization Middleware API
============================

Setup auth and autz
-------------------

.. autofunction:: aiohttp_auth.setup


Public Middleware API
---------------------

.. automodule:: aiohttp_auth.autz.autz
    :members: setup, autz_middleware, permit

Decorators
----------

.. automodule:: aiohttp_auth.autz.decorators
    :members:

ACL Authorization Policy
------------------------

.. automodule:: aiohttp_auth.autz.policy.acl

.. autoclass:: aiohttp_auth.autz.policy.acl.AbstractACLAutzPolicy
    :members:
    :special-members: __init__

.. autoclass:: aiohttp_auth.autz.policy.acl.AbstractACLContext
    :members:

.. autoclass:: aiohttp_auth.autz.policy.acl.NaiveACLContext
    :members:
    :special-members: __init__

.. autoclass:: aiohttp_auth.autz.policy.acl.NaiveACLContext
    :members:
    :special-members: __init__
    :inherited-members:


