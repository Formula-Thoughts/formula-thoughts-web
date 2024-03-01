import json
from typing import TypeVar, Type, Any, Callable

import punq

from formula_thoughts_web.abstractions import Serializer, Deserializer, Logger, ErrorHandlingStrategy
from formula_thoughts_web.application import TopLevelSequenceRunner, ErrorHandlingTypeState, ExceptionErrorHandlingStrategy, \
    ResponseErrorHandlingStrategy, ErrorHandlingStrategyFactory
from formula_thoughts_web.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer, ObjectMapper, JsonConsoleLogger
from formula_thoughts_web.events import EventRunner
from formula_thoughts_web.exceptions import EventSchemaInvalidException
from formula_thoughts_web.web import WebRunner, StatusCodeMapping


T = TypeVar('T')


class LambdaRunner:
    
    def __init__(self, web_runner: WebRunner,
                 event_runner: EventRunner,
                 logger: Logger):
        self.__logger = logger
        self.__event_runner = event_runner
        self.__web_runner = web_runner
        
    def run(self, event: dict, context: dict) -> dict:
        self.__logger.log_trace(message=str(event), properties={"action": "view_events"})
        self.__logger.log_trace(message=str(context), properties={"action": "view_context"})
        # TODO: improve validation, use information from context about request
        if 'routeKey' in event:
            self.__logger.add_global_properties(properties={"request_type": "api_handler"})
            return self.__web_runner.run(event=event)
        elif 'Records' in event:
            self.__logger.add_global_properties(properties={"request_type": "event_handler"})
            return self.__event_runner.run(event=event)
        else:
            raise EventSchemaInvalidException("schema does not match SQS event or API gateway")


class Container:

    def __init__(self):
        self.__container = punq.Container()

    def register(self, service: Type[T], implementation: Type[T] = None, scope: punq.Scope = punq.Scope.singleton) -> 'Container':
        if implementation is None:
            self.__container.register(service=service, scope=scope)
        else:
            self.__container.register(service, implementation, scope=scope)
        return self

    def register_factory(self, service: Type[T],
                         factory: Callable[[], T] = None,
                         scope: punq.Scope = punq.Scope.singleton) -> 'Container':
        self.__container.register(service=service, factory=factory, scope=scope)
        return self

    def resolve(self, service: Type[T]) -> T:
        return self.__container.resolve(service)

    def register_status_code_mappings(self, mappings: dict) -> 'Container':
        self.__container.register(service=StatusCodeMapping, scope=punq.Scope.singleton)
        status_mapping: StatusCodeMapping = self.__container.resolve(StatusCodeMapping)
        for code in mappings.keys():
            status_mapping.add_mapping(_type=code, status_code=mappings[code])
        return self


def register_web(services: Container, default_error_handling_strategy: str):
    services.register(service=ErrorHandlingStrategy, implementation=ExceptionErrorHandlingStrategy)
    services.register(service=ErrorHandlingStrategy, implementation=ResponseErrorHandlingStrategy)
    services.register(service=ErrorHandlingStrategyFactory)
    services.register_factory(service=ErrorHandlingTypeState,
                              factory=lambda: ErrorHandlingTypeState(
                                  default_error_handling_strategy=default_error_handling_strategy
                              ),
                              scope=punq.Scope.singleton)
    services.register(service=LambdaRunner)
    services.register(service=EventRunner)
    services.register(service=Serializer, implementation=JsonSnakeToCamelSerializer)
    services.register(service=Deserializer, implementation=JsonCamelToSnakeDeserializer)
    services.register(service=TopLevelSequenceRunner)
    services.register(service=WebRunner)
    services.register(service=ObjectMapper)
    services.register(service=Logger, implementation=JsonConsoleLogger)
    services.register(service=StatusCodeMapping, scope=punq.Scope.singleton)
