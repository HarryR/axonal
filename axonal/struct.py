class Target:
    __slots__ = ('service', 'version', 'method')

    def __init__(self, service: str, version: str, method: str):
        self.service = service
        self.version = version
        self.method = method


class Context:
    __slots__ = ('target', 'guid', 'auth', 'meta')

    def __init__(self, target: Target, guid: str, auth, meta):
        self.target = target
        self.guid = guid
        self.auth = auth
        self.meta = meta


class Event:
    __slots__ = ('context', 'args')

    def __init__(self, context: Context, args):
        self.context = context
        self.args = args

    @property
    def is_event(self):
        return True


class Request(Event):
    @property
    def is_event(self):
        return False


class Fault(Exception):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    INVALID_RESPONSE = -32604
    SERIALIZE_ERROR = -32605
    APPLICATION_ERROR = -32000
    SERVICE_UNKNOWN = -32001
    VERSION_UNKNOWN = -32002
    NOT_AUTHORISED = -32002
    __slots__ = ('context', 'code', 'message', 'data', 'inner')

    @classmethod
    def get_message(cls, code, default='Unknown fault!'):
        return FAULT_MESSAGES.get(code, default)

    def __init__(self, context, code, message=None, data=None, inner=None):
        if message is None:
            message = Fault.get_message(code)
        super().__init__(message, code)
        self.context = context
        self.code = code
        self.message = message
        self.data = data
        self.inner = inner


FAULT_MESSAGES = {
    Fault.PARSE_ERROR: 'Parse error',
    Fault.INVALID_REQUEST: 'Invalid request',
    Fault.METHOD_NOT_FOUND: 'Method not found',
    Fault.INVALID_PARAMS: 'Invalid params',
    Fault.INTERNAL_ERROR: 'Internal error',
    Fault.INVALID_RESPONSE: 'Invalid response',
    Fault.SERIALIZE_ERROR: 'Serialize error',
    Fault.APPLICATION_ERROR: 'Application error',
    Fault.SERVICE_UNKNOWN: 'Service name not found',
    Fault.VERSION_UNKNOWN: 'Service version not found',
    Fault.NOT_AUTHORISED: 'Not authorised'
}


class Response:
    __slots__ = ('context', 'data')

    def __init__(self, context, data):
        self.context = context
        self.data = data
