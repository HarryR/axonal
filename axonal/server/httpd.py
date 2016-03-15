import json
import sys
import aiohttp
import asyncio
import logging
from aiohttp import web

from .. import __version__
from ..plugin import Host, Plugin
from ..middleware.proxy import ServiceProxy
from ..struct import Fault
from ..utils import json_dumpb

LOGGER = logging.getLogger(__name__)


def _fault_code_to_http_status(code):
    mapping = {
        Fault.PARSE_ERROR: 400,
        Fault.INVALID_REQUEST: 400,
        Fault.METHOD_NOT_FOUND: 404,
        Fault.INVALID_PARAMS: 400,
        Fault.INTERNAL_ERROR: 500,
        Fault.INVALID_RESPONSE: 500,
        Fault.SERIALIZE_ERROR: 500,
        Fault.APPLICATION_ERROR: 500,
        Fault.SERVICE_UNKNOWN: 404,
        Fault.VERSION_UNKNOWN: 404,
        Fault.NOT_AUTHORISED: 401
    }
    return mapping.get(code, 500)


class FaultResponse(web.Response):
    """
    Responds with a JSON encoded Fault and appropriate error code
    """

    def __init__(self, fault):
        status = _fault_code_to_http_status(fault.code)
        body = json_dumpb({'error': [status, fault.message]})
        super().__init__(
            body=body,
            status=status,
            reason=Fault.get_message(fault.code),
            content_type='application/json',
        )


class RpcHttpApp(web.Application):
    def __init__(self, broker):
        super().__init__()
        self.broker = broker
        self.router.add_route('GET', '/svc/{service}/{version}/{method}', self.handle_call_GET)
        self.router.add_route('POST', '/svc/{service}/{version}/{method}', self.handle_call_POST)
        self.on_response_prepare.append(self._on_prepare)

    def _on_prepare(self, request, response):
        response.headers[aiohttp.hdrs.SERVER] = 'Axonal/%s' % (__version__)

    def _dispatch(self, request, raw_params):
        service = request.match_info.get('service')
        version = request.match_info.get('version')
        method = request.match_info.get('method')
        params = {key: raw_params.get(key)
                  for key in frozenset(raw_params.keys())}
        proxy = ServiceProxy(self.broker, service, version)
        target = getattr(proxy, method)
        try:
            # XXX: What happens if result is None?
            if isinstance(params, (tuple, list)):
                result = target(*params)
            else:
                result = target(**params)
            return web.Response(
                body=json_dumpb(result),
                content_type='application/json',
            )
        except Fault as fault:
            return FaultResponse(fault)
        except Exception:
            raise

    async def handle_call_GET(self, request):
        try:
            return self._dispatch(request, request.GET)
        except Exception:
            logging.exception('Derp GET')

    async def handle_call_POST(self, request):
        try:
            post_data = await request.post()
            return self._dispatch(request, post_data)
        except Exception:
            logging.exception('Derp POST')


class RpcHttpPlugin(Plugin):
    async def _setup(self, loop):
        from ..registry import register, GlobalRegistry
        from ..middleware.broker import RegistryBroker

        @register('test.derp', '1.3.5')
        class DerpService(object):
            def echo(self, val):
                return val

        app = RpcHttpApp(RegistryBroker(GlobalRegistry()))
        handler = app.make_handler()
        srv = await loop.create_server(handler, '127.0.0.1', 8080)
        return srv, handler

    def run(self):
        loop = asyncio.get_event_loop()
        srv, handler = loop.run_until_complete(self._setup(loop))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.run_until_complete(handler.finish_connections())


if __name__ == "__main__":
    Host(RpcHttpPlugin()).main(sys.argv[1:])
