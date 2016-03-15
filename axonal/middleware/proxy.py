from uuid import uuid4
from ..struct import Request, Context, Target


class ProxyMethod(object):
    def __init__(self, broker, target, auth=None, meta=None):
        self.broker = broker
        self.target = target
        self.auth = auth
        self.meta = meta

    def __call__(self, *arg, **kwa):
        guid = str(uuid4())
        ctx = Context(self.target, guid, self.auth, self.meta)
        args = arg if len(arg) else kwa
        request = Request(ctx, args)
        return self.broker.dispatch(request).data


class ServiceProxy(object):
    __slots__ = ('_broker', '_service', '_version', '_auth', '_meta',
                 '_methods')

    def __init__(self, broker, service, version, auth=None, meta=None):
        self._broker = broker
        self._service = service
        self._version = version
        self._auth = auth
        self._meta = meta
        self._methods = dict()

    def __getattr__(self, key):
        if key[0] == '_':
            raise AttributeError()
        if key in self._methods:
            return self._methods[key]
        target = Target(self._service, self._version, key)
        method = ProxyMethod(self._broker, target, self._auth, self._meta)
        self._methods[key] = method
        return method
