"""
The service layer creates a way for exposing methods from Python classes
over a distributed message queue, the Transport (message queue) and
RPC protocol are interchangeable, but initially only NATS.io and JSON-RPC
are supported.

The Python classes exposed are POPOs with a few semantic annotations
to ensure correct operation. The Python class implements a named and
versioned API, for example com.logicista.example(1.3). To connect to
other services it's given a context at initilisation.

== Decorators

@service.register('srv.example', ['1.2', '1.3.5'])
class ExampleService(object):
    events = service.DependsOn('srv.events', '1')

    @asyncio.coroutine
    def echo(self, arg):
        yield from self.events.emit('Echo called', arg)
        return 'arg'

In this example the ServiceManager will listen on the following channels:

   srv.example.1.3.5
   srv.example.1.3.X
   srv.example.1.2.X
   srv.example.1.X.X

The queue group will be 'srv.example'

Calls sent to `event` will be published to the 'srv.events.1.X' channel and
delivered to at-most one member of the 'srv.events' queue group.


service.
    registry.
        register
        Registry
    Meta
    DependsOn
    PushesTo

dispatcher.
    JsonRpcProtocol
    JsonEventProtocol
    NatsDispatcher
        - takes RpcProtocol
        - takes EventProtocol
    RegistryDispatcher
        - takes Registry

"""

from collections import defaultdict
import re
from .utils import Singleton

__all__ = ('register', 'Registry', 'GlobalRegistry')


def _validate_name(name):
    if name is None:
        raise ValueError('No service name')
    if not re.match(r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$', name):
        raise ValueError('Service name is invalid: %s' % (name,))
    return name


def _validate_versions(versions):
    assert isinstance(versions, (list, set, str))
    if isinstance(versions, str):
        versions = [versions]
    versions = list(versions)
    out = []
    for ver in versions:
        ver = str(ver)
        if not ver or not re.match(r'[0-9](\.[0-9X](\.([a-f0-9]+|X))?)?', ver):
            raise ValueError('Invalid version: %s' % (ver,))
        out.append(ver)
    return out


def _expand_versions(versions):
    """
    Converts a list of one or more semantic versions into
    a sorted list of 'semantically compatible' versions.

        1.3.5 = 1.3.5, 1.3.X, 1.X.X
        1.2 = 1.2.X, 1.X.X
        1 = 1.X.X
    """
    assert isinstance(versions, (list, set, str))
    versions = list(versions)
    output = list()
    for ver in versions:
        split = ver.split('.')
        if len(split) < 2:
            split.append('X')
        if len(split) < 3:
            split.append('X')
        output.append('.'.join([split[0], split[1], split[2]]))
        output.append('.'.join([split[0], split[1], 'X']))
        output.append('.'.join([split[0], 'X', 'X']))
    return sorted(list(set(output)))


def _service_name_versions(service_cls):
    name = _validate_name(getattr(service_cls, '_service_name'))
    versions = _validate_versions(getattr(service_cls, '_service_versions'))
    if not len(versions):
        raise RuntimeError('Service has no versions: %r' % (service_cls,))
    return name, versions


def register(name, versions):
    """
    Registers a service providing class
    """
    name = _validate_name(name)
    versions = _validate_versions(versions)

    def class_registrator(cls):
        cls._service_versions = versions
        cls._service_name = name
        GlobalRegistry().add(cls)
        return cls
    return class_registrator


class Registry(object):
    services = defaultdict(dict)
    classes = list()

    def add(self, service_cls):
        if service_cls in self.classes:
            raise RuntimeError('Class registered twice: %r' % (service_cls,))
        name, versions = _service_name_versions(service_cls)
        for ver in _expand_versions(versions):
            if ver in self.services[name]:
                raise RuntimeError('Service version conflict: %s - %s' % (
                    name, ver))
            self.services[name][ver] = service_cls
        self.classes.append(service_cls)

    def lookup(self, name, versions=None):
        assert isinstance(name, str)
        if name not in self.services:
            raise RuntimeError('Service not found: %s' % (name,))
        instances = self.services[name]
        if versions:
            # Get the highest available version requested
            versions = _validate_versions(versions)
            for ver in _expand_versions(versions):
                ret = instances.get(ver)
                if ret:
                    return ret
        else:
            # Get the latest available version
            all_versions = sorted(list(instances.keys()))
            if len(all_versions):
                return all_versions[0]

    def remove(self, service_cls):
        if service_cls not in self.classes:
            raise RuntimeError('Service not found: %r' % (service_cls,))
        name, versions = _service_name_versions(service_cls)
        self.classes.remove(service_cls)
        for ver in _expand_versions(versions):
            del self.services[name][ver]


class GlobalRegistry(Singleton, Registry):
    pass
