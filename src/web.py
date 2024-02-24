from abc import ABC
from typing import Type

from src.abstractions import SequenceBuilder, ApplicationContext, RequestHandler, Serializer, Logger, Deserializer
from src.application import TopLevelSequenceRunner


class StatusCodeMapping:

    def __init__(self):
        self.__mappings = {}

    def add_mapping(self, _type, status_code: int) -> None:
        self.__mappings[f"{_type.__module__}.{_type.__name__}"] = status_code

    def get_mappings(self, response: Type) -> int:
        return self.__mappings[f"{response.__module__}.{response.__name__}"]


class WebRunner:

    def __init__(self,
                 request_handlers: list[RequestHandler],
                 serializer: Serializer,
                 status_code_mappings: StatusCodeMapping,
                 logger: Logger):
        self.__status_code_mappings = status_code_mappings
        self.__logger = logger
        self.__serializer = serializer
        self.__request_handlers = request_handlers

    def run(self, event) -> dict:
        headers = {"Content-Type": "application/json"}
        request_handler_matches = list(filter(lambda x: x.route_key == event['routeKey'], self.__request_handlers))
        if len(request_handler_matches) == 0:
            return {
                "headers": headers,
                "body": self.__serializer.serialize(data={"message": f"route {event['routeKey']} not found"}),
                "statusCode": 404
            }
        try:
            context: ApplicationContext = request_handler_matches[0].run(event=event)
            body = None
            status_code = 204
            if context.response is not None:
                body = self.__serializer.serialize(data=context.response.__dict__)
                status_code = self.__status_code_mappings.get_mappings(response=type(context.response))
            return {
                "headers": headers,
                "body": body,
                "statusCode": status_code
            }
        except Exception as e:
            self.__logger.log_exception(exception=e)
            return {
                "headers": headers,
                "body": self.__serializer.serialize(data={"message": f"internal server error :("}),
                "statusCode": 500
            }


class ApiRequestHandlerBase(ABC):

    def __init__(self, route_key: str,
                 sequence: SequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        self.__deserializer = deserializer
        self.__command_pipeline = command_pipeline
        self.__route_key = route_key
        self.__sequence = sequence

    def run(self, event: dict) -> ApplicationContext:
        body = None
        auth_user_id = None
        parameters = {}
        if 'pathParameters' in event:
            path_parameters = event['pathParameters']
            if path_parameters is None:
                pass
            parameters = {**parameters, **path_parameters}
        if 'queryStringParameters' in event:
            query_parameters = event['queryStringParameters']
            if query_parameters is None:
                pass
            parameters = {**parameters, **query_parameters}
        try:
            auth_user_id = event['requestContext']['authorizer']['jwt']['claims']['name']
        except KeyError:
            pass
        if 'body' in event:
            try:
                json_body = self.__deserializer.deserialize(event['body'])
                body = json_body
            except ValueError:
                body = event['body']
        context = ApplicationContext(body=body,
                                     auth_user_id=auth_user_id,
                                     parameters=parameters,
                                     error_capsules=[])
        self.__command_pipeline.run(context=context,
                                    top_level_sequence=self.__sequence)
        return context

    @property
    def route_key(self) -> str:
        return self.__route_key
