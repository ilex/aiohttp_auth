aiohttp_auth_autz
=================

.. image:: https://travis-ci.org/ilex/aiohttp_auth_autz.svg?branch=master
    :target: https://travis-ci.org/ilex/aiohttp_auth_autz

.. image:: https://readthedocs.org/projects/aiohttp-auth-autz/badge/?version=latest
    :target: http://aiohttp-auth-autz.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

This library provides authorization and authentication middleware plugins for
aiohttp servers.

These plugins are designed to be lightweight, simple, and extensible, allowing
the library to be reused regardless of the backend authentication mechanism.
This provides a familiar framework across projects.

There are three middleware plugins provided by the library. The ``auth_middleware``
plugin provides a simple system for authenticating a users credentials, and
ensuring that the user is who they say they are.

The ``autz_middleware`` plugin provides a generic way of authorization using 
different authorization policies. There is the ACL authorization policy as a
part of the plugin.

The ``acl_middleware`` plugin provides a simple access control list authorization
mechanism, where users are provided access to different view handlers depending
on what groups the user is a member of. It is recomended to use ``autz_middleware``
with ACL policy instead of this middleware.

This is a fork of `aiohttp_auth <https://github.com/gnarlychicken/aiohttp_auth>`_
library that fixes some bugs and security issues and also introduces a generic 
authorization ``autz`` middleware with built in ACL authorization policy.


Documentation
-------------

http://aiohttp-auth-autz.readthedocs.io/


Install
-------

Install ``aiohttp_auth_autz`` using ``pip``::

    $ pip install aiohttp_auth_autz


Getting Started
---------------

.. include:: docs/getting-started.rst

License
-------

The library is licensed under a MIT license.
