import json
import pickle
import msgpack
from typing import Union

from ..struct import Event, Request, Response, Fault, Context, Target
from ..interface import Protocol
from ..utils import json_dumps

__all__ = ('BaseInternalProtocol', 'JsonInternalProtocol',
           'PickleInternalProtocol')


class BaseInternalProtocol(Protocol):
    def _to_msg(self, obj: Union[Fault, Request, Event, Response]):
        assert isinstance(obj, (Request, Response, Fault, Event))
        msg = dict()
        if isinstance(obj, Request):
            code = 'Q'
            msg['A'] = obj.args
        elif isinstance(obj, Event):
            code = 'E'
            msg['A'] = obj.args
        elif isinstance(obj, Response):
            code = 'R'
            msg['D'] = obj.data
        elif isinstance(obj, Fault):
            code = 'F'
            msg['X'] = [obj.code, obj.message, obj.data]
        else:
            raise TypeError('Cannot encode unknown type')
        msg['V'] = '1'
        msg['_'] = code
        ctx = obj.context
        msg['T'] = [ctx.target.service, ctx.target.version, ctx.target.method]
        msg['C'] = [ctx.guid, ctx.auth, ctx.meta]
        return msg

    def _from_msg(self, msg: dict) -> Union[Fault, Request, Event, Response]:
        """
        Converts a message dictionary from its internal representation into
        a native object of the appropriate type.
        """
        if msg.get('V') != '1':
            raise Fault(Fault.PARSE_ERROR, 'Unknown proto version')
        obj_type = msg.get('_')
        if obj_type not in ('Q', 'R', 'F', 'E'):
            raise Fault(Fault.PARSE_ERROR, 'Invalid proto obj type')
        obj_tgt = msg.get('T')
        obj_ctx = msg.get('C')
        if not all([obj_type, obj_tgt, obj_ctx]):
            raise Fault(Fault.PARSE_ERROR, 'Missing proto fields')
        for field in (obj_tgt, obj_ctx):
            if not isinstance(field, (tuple, list)):
                raise Fault(Fault.PARSE_ERROR, 'Invalid ctx or tgt types')
            if len(field) != 3:
                raise Fault(Fault.PARSE_ERROR, 'Invalid ctx or tgt lengths')
        target = Target(obj_tgt[0], obj_tgt[1], obj_tgt[2])
        context = Context(target, obj_ctx[0], obj_ctx[1], obj_ctx[2])
        if obj_type in ('Q', 'E'):
            obj_args = msg.get('A')
            if not isinstance(obj_args, (tuple, list, dict)):
                raise Fault(Fault.PARSE_ERROR, 'Invalid request args')
            if obj_type == 'Q':
                return Request(context, obj_args)
            else:
                return Event(context, obj_args)
        elif obj_type == 'R':
            return Response(context, msg.get('D'))
        elif obj_type == 'F':
            obj_exc = msg.get('X')
            if not isinstance(obj_exc, (tuple, list)) or len(obj_exc) != 3:
                raise Fault(Fault.PARSE_ERROR, 'Invalid fault data')
            return Fault(context, obj_exc[0], obj_exc[1], obj_exc[2])


class JsonInternalProtocol(BaseInternalProtocol):
    def encode(self, obj):
        try:
            return json_dumps(self._to_msg(obj))
        except Exception as ex:
            raise Fault(Fault.SERIALIZE_ERROR, 'JSON serialize', inner=ex)

    def decode(self, data):
        try:
            msg = json.loads(data)
        except Exception as ex:
            raise Fault(Fault.PARSE_ERROR, 'JSON parse', inner=ex)
        return self._from_msg(msg)


class PickleInternalProtocol(BaseInternalProtocol):
    def __init__(self, pickle_protocol=-1):
        self.pickle_protocol = pickle_protocol

    def encode(self, obj):
        try:
            return pickle.dumps(self._to_msg(obj), self.pickle_protocol)
        except Exception as ex:
            raise Fault(Fault.SERIALIZE_ERROR, 'Pickle serialize', inner=ex)

    def decode(self, data):
        try:
            msg = pickle.loads(data)
        except Exception as ex:
            raise Fault(Fault.PARSE_ERROR, 'Pickle parse', inner=ex)
        return self._from_msg(msg)

class MsgpackInternalProtocol(BaseInternalProtocol):
    def encode(self, obj):
        try:
            return msgpack.unpackb(self._to_msg(obj))
        except Exception as ex:
            raise Fault(Fault.SERIALIZE_ERROR, 'Msgpack serialize', inner=ex)

    def decode(self, data):
        try:
            msg = msgpack.packb(data)
        except Exception as ex:
            raise Fault(Fault.PARSE_ERROR, 'Msgpack parse', inner=ex)
        return self._from_msg(msg)

