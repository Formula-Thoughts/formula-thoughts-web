import inspect
import json
import re
import typing
from datetime import datetime
from decimal import Decimal
from enum import Enum

import dateutil

from formula_thoughts_web.abstractions import Serializer
from formula_thoughts_web.exceptions import MappingException


class LogSeverity(Enum):
    ERROR = "ERROR"
    EVENT = "EVENT"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"


class JsonConsoleLogger:

    def __init__(self, serializer: Serializer):
        self.__serializer = serializer
        self.__request_props = {}

    def __log(self, _type: LogSeverity, message: str, properties: dict):
        if properties is None:
            properties = {}
        _function = inspect.stack()[2].function
        _class = "None"
        _module = "Unknown"
        try:
            _class = type(inspect.stack()[2].frame.f_locals['self']).__name__
            _module = type(inspect.stack()[2].frame.f_locals['self']).__module__
        except:
            ...
        name = f"{_module}.{_class}.{_function}"
        message = {
            "message": message,
            "severity": str(_type),
            "location": name
        }
        log_message = {**message, **self.__request_props, **properties}
        print(f"{self.__serializer.serialize(log_message)}")

    def add_global_properties(self, properties: dict):
        self.__request_props = properties

    def log_error(self, message: str, properties: dict = None):
        self.__log(_type=LogSeverity.ERROR, message=message, properties=properties)

    def log_exception(self, exception: Exception, properties: dict = None):
        self.__log(_type=LogSeverity.ERROR, message=str(exception), properties=properties)

    def log_info(self, message: str, properties: dict = None):
        self.__log(_type=LogSeverity.INFO, message=message, properties=properties)

    def log_event(self, message: str, properties: dict = None):
        self.__log(_type=LogSeverity.EVENT, message=message, properties=properties)

    def log_debug(self, message: str, properties: dict = None):
        self.__log(_type=LogSeverity.DEBUG, message=message, properties=properties)

    def log_trace(self, message: str, properties: dict = None):
        self.__log(_type=LogSeverity.TRACE, message=message, properties=properties)


def all_annotations(cls):
    d = {}
    for c in cls.mro():
        try:
            d.update(**c.__annotations__)
        except AttributeError:
            # object, at least, has no __annotations__ attribute.
            pass
    return d


T = typing.TypeVar("T")


class ObjectMapper:

    def map_to_dict_and_ignore_none_fields(self, _from, to: typing.Type[T]) -> dict:
        print(f"{vars(_from).items()}")
        mapped = self.__generic_map(_from=_from,
                                    to=to,
                                    propValues=vars(_from).items())
        new_dict = mapped.__dict__
        self.__to_dict_and_ignore_none_fields(new_dict=new_dict, mapped=mapped)
        return new_dict

    def __to_dict_and_ignore_none_fields(self, new_dict: dict, mapped):
        for property, value in list(new_dict.items()):
            try:
                if bool(typing.get_type_hints(getattr(mapped, property))):
                    self.__to_dict_and_ignore_none_fields(
                        new_dict=value,
                        mapped=getattr(mapped, property))
            except TypeError:
                print(f"value {property} skipped")
            if value is None:
                new_dict.pop(property)

    def map(self, _from, to: typing.Type[T]) -> T:
        print(f"{vars(_from).items()}")
        return self.__generic_map(_from=_from,
                                  to=to,
                                  propValues=vars(_from).items(),
                                  map_to=lambda x, y: self.map(_from=x, to=y))

    def map_from_dict(self, _from, to: typing.Type[T]) -> T:
        print(_from.items())
        return self.__generic_map(_from=_from,
                                  to=to,
                                  propValues=_from.items(),
                                  map_to=lambda x, y: self.map_from_dict(_from=x, to=y))

    def map_to_dict(self, _from, to: typing.Type[T], preserve_decimal=False) -> dict:
        print(f"{vars(_from).items()}")
        return self.__generic_map(_from=_from,
                                  to=to,
                                  propValues=vars(_from).items(),
                                  map_callback=lambda x: self.to_dict(x, preserve_decimal=preserve_decimal),
                                  map_to=lambda x, y: self.map_to_dict(_from=x, to=y))

    def to_dict(self, obj, preserve_decimal):
        return json.loads(json.dumps(obj, default=lambda o: self.default_json_converter(o, preserve_decimal)))

    @staticmethod
    def default_json_converter(object, preserve_decimal):
        if type(object) == Decimal:
            if preserve_decimal:
                return str(object)
            else:
                return float(str(object))
        elif type(object) == datetime:
            return object.isoformat()
        else:
            return object.__dict__

    def __generic_map(self, _from, to, propValues, map_to, map_callback=lambda x: x):
        try:
            new_dto = to()
            dict_to = all_annotations(to)
            print("START MAPPING")
            print(f"all annotations from DTO {dict_to}")
            print(f"all props from _from {propValues}")
            for property, value in propValues:
                if property in dict_to:
                    if bool(typing.get_type_hints(dict_to[property])):
                        setattr(new_dto, property, map_callback(map_to(value, dict_to[property])))
                    elif (typing.get_origin(dict_to[property]) is list and
                          (bool(typing.get_type_hints(typing.get_args(dict_to[property])[0])))):
                        collection = []
                        sub_item_to = typing.get_args(dict_to[property])[0]
                        for item in value:
                            collection.append(map_callback(map_to(item, sub_item_to)))
                        setattr(new_dto, property, collection)
                    elif dict_to[property] is datetime and type(value) is str:
                        new_dto.__dict__[property] = datetime.fromisoformat(value)
                    elif dict_to[property] is Decimal:
                        if type(value) is str:
                            new_dto.__dict__[property] = Decimal(value)
                        elif type(value) is float:
                            new_dto.__dict__[property] = Decimal(str(value))
                        else:
                            new_dto.__dict__[property] = value
                    elif dict_to[property] == list[Decimal]:
                        decimals = []
                        for item in value:
                            if type(item) is str:
                                decimals.append(Decimal(item))
                            elif type(item) is float:
                                decimals.append(Decimal(str(item)))
                            else:
                                decimals.append(item)
                            new_dto.__dict__[property] = decimals
                    else:
                        new_dto.__dict__[property] = value
            print(f"__generic_map from {type(_from)} {to} and mapped {_from} out -> {new_dto}")
            return map_callback(new_dto)
        except Exception as e:
            raise MappingException(str(e))


class JsonSnakeToCamelSerializer:

    def serialize(self, data: typing.Union[dict, list]) -> str:
        return json.dumps(self.__snake_case_to_camel_case_dict(d=data), default=str)

    def __snake_case_to_camel_case_dict(self, d):
        if isinstance(d, list):
            return [self.__snake_case_to_camel_case_dict(i) if isinstance(i, (dict, list)) else self.__format_value(i)
                    for i in d]
        return {self.__snake_case_key_to_camel_case(a): self.__snake_case_to_camel_case_dict(b) if isinstance(b, (
            dict, list)) else self.__format_value(b) for a, b in d.items()}

    @staticmethod
    def __format_value(value) -> typing.Any:
        if (isinstance(value, Enum)):
            return value.value
        return value

    @staticmethod
    def __snake_case_key_to_camel_case(key: str) -> str:
        components = key.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])


class JsonCamelToSnakeDeserializer:

    def deserialize(self, data: str) -> typing.Union[dict, list]:
        data_dict = json.loads(data)
        return self.__camel_case_to_snake_case_dict(d=data_dict)

    def __camel_case_to_snake_case_dict(self, d):
        if isinstance(d, list):
            return [self.__camel_case_to_snake_case_dict(i) if isinstance(i, (dict, list)) else i for i in d]
        return {self.__camel_case_key_to_snake_case(a): self.__camel_case_to_snake_case_dict(b) if isinstance(b, (
            dict, list)) else b for a, b in d.items()}

    @staticmethod
    def __camel_case_key_to_snake_case(key: str) -> str:
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]{1,}(?=[A-Z][a-z]|\d|\W|$)|\d+', key)
        return '_'.join(map(str.lower, words))
