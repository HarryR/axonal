import pytest
from axonal.middleware.broker import Router, RegistryBroker

from axonal.registry import GlobalRegistry, register
from axonal.struct import Fault
from axonal.middleware.proxy import ServiceProxy


@register('test.derp', '1.3.5')
class DerpService(object):
    def echo(self, val):
        return val


def test_derp():
    router = Router([
        RegistryBroker(GlobalRegistry())
    ])
    proxy = ServiceProxy(router, 'test.derp', '1')
    assert proxy.echo('derp') == 'derp'
    with pytest.raises(Fault) as excinfo:
        proxy.merp()
    assert excinfo.value.code == Fault.METHOD_NOT_FOUND


def test_protoproxy():
    from axonal.middleware.dispatcher import (ProtocolTransportDispatcher,
                                       ProtocolDispatcherTransport)
    from axonal.proto.internal import JsonInternalProtocol
    json_proto = JsonInternalProtocol()

    registry = RegistryBroker(GlobalRegistry())
    local_transport = ProtocolDispatcherTransport(json_proto, registry)
    router = Router([
        ProtocolTransportDispatcher(json_proto, local_transport)
    ])
    proxy = ServiceProxy(router, 'test.derp', '1')
    assert proxy.echo('derp') == 'derp'
