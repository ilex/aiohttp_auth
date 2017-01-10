"""Test utilites."""
import sys
import traceback
from aiohttp import web


async def assert_middleware(app, handler):
    """Collect AssertionError in handler.

    Use this middleware to collect assertion errors in
    aiohttp handlers. Formatted error will be passed as
    text to web.Response.
    """
    async def middleware_handler(request):
        try:
            response = await handler(request)
        except AssertionError as e:
            _, _, tb = sys.exc_info()
            # traceback.print_tb(tb) # Fixed format
            tb_info = traceback.extract_tb(tb)
            filename, line, func, text = tb_info[-1]
            message = '\n{0}:{1}\n> {2}\nE {3}\n'.format(
                filename, line, text, str(e)
            )
            return web.Response(text=message)

        return response

    return middleware_handler


async def assert_response(request, response_text):
    """Helper function to reraise assertion errors from handlers if any.

    This function can be used in cooperation with assert_middleware
    to reraise AssertionError from aiohttp handlers as follow::

        async def test_something(app, client):
            async def handler_test(request):
                assert False  # when test fail we will see this line.
                return web.Response(text='text')

            app.router.add_get('/test', handler_test)
            cli = await client(app)

            # Note missed await before cli.get
            response = await assert_response(cli.get('/test'), 'test')

    Testing this with py.test give us right place of the assertion
    error if any.

    Args:
        request: awaitable request.
        response_text: excepted text in response.

    Returns:
        ClientResponse: response for given request.

    Raises:
        AssertionError: when it was assertion error in tested hanlder.
    """
    response = await request
    text = await response.text()
    if text != response_text:
        raise AssertionError(text)

    return response
