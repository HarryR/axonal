from ..struct import Request, Response, Fault, Event
from ..interface import Dispatcher, Protocol, Transport


class BaseDispatcher(Dispatcher):
    def dispatch(self, request):
        assert isinstance(request, (Request, Event))
        if request.is_event:
            return self.emit(request)
        else:
            return self.call(request)

    def emit(self, request):
        """
        Dispatch a request, with no expectation of a reply
        """
        assert isinstance(request, Event)
        raise NotImplementedError()

    def call(self, request):
        """
        Dispatch a request, with synchronous reply
        """
        assert isinstance(request, Request)
        raise NotImplementedError()

    def _handle_exception(self, request, ex, default_code=None):
        if default_code is None:
            default_code = Fault.INTERNAL_ERROR
        if isinstance(ex, Fault):
            # TODO: validate if the context is the same?
            return Fault(request.context, ex.code, ex.message, ex.data)
        elif isinstance(ex, NotImplementedError):
            return Fault(request.context, Fault.METHOD_NOT_FOUND, inner=ex)
        elif isinstance(ex, (RuntimeError, ValueError, TypeError)):
            return Fault(request.context, Fault.APPLICATION_ERROR,
                         str(ex.args[0]), inner=ex)
        elif isinstance(ex, Exception):
            return Fault(request.context, Fault.APPLICATION_ERROR, inner=ex)
        else:
            return Fault(request.context, default_code, inner=ex)


class ClassInstanceDispatcher(BaseDispatcher):
    """
    Dispatches method calls to a local class instance
    """
    __slots__ = ('instance',)

    def __init__(self, instance):
        assert instance is not None
        self.instance = instance

    def can_dispatch(self, request):
        return True

    def emit(self, request):
        assert isinstance(request, Event)
        assert request.is_event
        return self._dispatch(request)

    def call(self, request):
        assert isinstance(request, Request)
        assert not request.is_event
        return self._dispatch(request)

    def _dispatch(self, request):
        method_name = request.context.target.method
        method = getattr(self.instance, method_name, None)
        if method is None or not callable(method):
            raise Fault(request.context, Fault.METHOD_NOT_FOUND)
        kwargs = dict()
        args = []
        if isinstance(request.args, dict):
            kwargs = request.args
        elif isinstance(request.args, (tuple, list)):
            args = list(request.args)
        # Then dispatch the call and handle exceptions
        try:
            result = method(*args, **kwargs)
        except Exception as ex:
            raise self._handle_exception(request, ex)
        # When all is good, return the result response
        if isinstance(request, Request):
            return Response(request.context, result)


class ProtocolDispatcherTransport(Transport):
    def __init__(self, protocol, dispatcher):
        self.protocol = protocol
        self.dispatcher = dispatcher

    def can_transport(self, request):
        return request is not None

    def send_request(self, context, data):
        obj = self.protocol.decode(data)
        resp = self.dispatcher.dispatch(obj)
        return self.protocol.encode(resp)

    def send_event(self, context, data):
        obj = self.protocol.decode(data)
        self.dispatcher.dispatch(obj)


class ProtocolTransportDispatcher(BaseDispatcher):
    """
    Dispatches method calls by encoding them with a protocol
    and asking a transport to handle the invocation.
    """
    __slots__ = ('protocol', 'transport')

    def __init__(self, protocol, transport):
        assert isinstance(protocol, Protocol)
        self.protocol = protocol
        self.transport = transport

    def can_dispatch(self, request):
        return self.transport.can_transport(request)

    def emit(self, request):
        assert isinstance(request, Event)
        data = self.protocol.encode_event(request)
        try:
            self.transport.send_event(request.context, data)
        except Exception as ex:
            raise self._handle_exception(request, ex, Fault.INTERNAL_ERROR)

    def call(self, request):
        assert isinstance(request, Request)
        try:
            data = self.protocol.encode(request)
        except Exception as ex:
            raise self._handle_exception(request, ex, Fault.PARSE_ERROR)
        try:
            response_data = self.transport.send_request(request.context, data)
        except Exception as ex:
            raise self._handle_exception(request, ex, Fault.INTERNAL_ERROR)
        try:
            result = self.protocol.decode(response_data)
        except Exception as ex:
            raise self._handle_exception(request, ex, Fault.PARSE_ERROR)
        if isinstance(result, Exception):
            raise self._handle_exception(request.context, result)
        elif isinstance(result, Response):
            return result
        return Response(request.context, result)
