class Dispatcher:
    def can_dispatch(self, request):
        raise NotImplementedError()

    def dispatch(self, request):
        raise NotImplementedError()


class Transport:
    def can_transport(self, request):
        pass

    def send_request(self, context, data):
        raise NotImplementedError()

    def send_event(self, context, data):
        raise NotImplementedError()


class Protocol:
    def encode(self, obj):
        raise NotImplementedError()

    def decode(self, data):
        raise NotImplementedError()
