import json

class _Singleton(type):
    """
    A metaclass that creates a Singleton base class when called.
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwa):  # noqa
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwa)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass


def json_default(o):
    if hasattr(o, 'to_dict'):
        return o.to_dict()
    elif hasattr(o, 'isoformat'):
        # Yes, UTC support only for now.
        return o.replace(microsecond=0).isoformat() + 'Z'
    else:
        raise TypeError(repr(o) + " is not JSON serializable")


def json_dumps(obj):
    return json.dumps(obj, default=json_default, ensure_ascii=True)

def json_dumpb(obj):
    return json_dumps(obj).encode('utf-8')