.. aiohttp_auth_autz documentation master file, created by
   sphinx-quickstart on Sun Feb 12 19:19:36 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to aiohttp_auth_autz's documentation!
=============================================

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

Install
-------

Install ``aiohttp_auth_autz`` using ``pip``::

    $ pip install aiohttp_auth_autz


License
-------
The library is licensed under a MIT license.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   getting-started
   middleware
   api/index
   CHANGELOG



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
