from .dispatcher import ClassInstanceDispatcher
from ..struct import Fault
from ..interface import Dispatcher


class Router(Dispatcher):
    def __init__(self, brokers):
        assert isinstance(brokers, list)
        self.brokers = brokers

    def can_dispatch(self, request):
        for broker in self.brokers:
            if broker.can_dispatch(request):
                return True
        return False

    def dispatch(self, request):
        for broker in self.brokers:
            if broker.can_dispatch(request):
                return broker.dispatch(request)
        raise Fault(request.context, Fault.SERVICE_UNKNOWN)


class RegistryBroker(Dispatcher):
    def __init__(self, registry):
        self.registry = registry
        self.instances = dict()
        self.services = dict()

    def _load(self, key, cls):
        instance = ClassInstanceDispatcher(cls())
        self.services[key] = instance
        if cls in self.instances:
            self.instances[cls] = self.instances[cls] | {key}
        return instance

    def _lookup(self, request):
        target = request.context.target
        key = (target.service, target.version)
        instance = self.services.get(key)
        if not instance:
            cls = self.registry.lookup(target.service, target.version)
            if cls:
                instance = self._load(key, cls)
        return instance

    def can_dispatch(self, request):
        instance = self._lookup(request)
        return instance is not None and instance.can_dispatch(request)

    def dispatch(self, request):
        instance = self._lookup(request)
        if instance:
            return instance.dispatch(request)
        raise Fault(request.context, Fault.SERVICE_UNKNOWN)
