Authentication Middleware API
=============================

Public Middleware API
---------------------

.. automodule:: aiohttp_auth.auth.auth
    :members: setup, auth_middleware, get_auth, remember, forget

Decorators
----------

.. automodule:: aiohttp_auth.auth.decorators
    :members:

Abstract Authentication Policy
------------------------------

.. autoclass::  aiohttp_auth.auth.abstract_auth.AbstractAuthentication
    :members:

Abstract Ticket Authentication Policy
-------------------------------------

.. autoclass:: aiohttp_auth.auth.ticket_auth.TktAuthentication
    :members:
    :special-members: __init__


Concrete Ticket Authentication Policies
---------------------------------------

.. autoclass:: aiohttp_auth.auth.cookie_ticket_auth.CookieTktAuthentication
    :members:
    :special-members: __init__
    :inherited-members: __init__

.. autoclass:: aiohttp_auth.auth.session_ticket_auth.SessionTktAuthentication
    :members:
    :special-members: __init__
    :inherited-members: __init__
