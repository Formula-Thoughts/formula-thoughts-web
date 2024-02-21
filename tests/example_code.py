from typing import Protocol

import punq
from simple_injection import ServiceCollection

from src.abstractions import Command, ApplicationContext, Logger, SequenceBuilder, Serializer, Deserializer, \
    RequestHandler
from src.application import FluentSequenceBuilder, TopLevelSequenceRunner
from src.ioc import register_web
from src.web import RequestHandlerBase, WebRunner
from tests import DummyLogger


def register_dependencies(services: punq.Container) -> None:
    services.register(BakingService)
    services.register(CreateBreadCommand, CreateWheatBreadCommand)
    services.register(PublishBreadNotificationCommand, PublishWheatBreadNotificationCommand)
    services.register(CreateBreadSequenceBuilder, CreateWheatBreadSequenceBuilder)
    services.register(RequestHandler, CreateBreadRequestHandlerInternal)
    services.register(RequestHandler, CreateBreadRequestHandler)
    services.register(Logger, DummyLogger)


def handler(event, context):
    ioc = punq.Container()
    register_web(services=ioc)
    register_dependencies(services=ioc)
    web_runner = ioc.resolve(service_key=WebRunner)
    web_runner.run(event=event)


class BakingService:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def do_stuff(self):
        self.__logger.log_info(message="baking bread")
        self.__logger.log_info(message="baked bread")


class CreateBreadSequenceBuilder(SequenceBuilder, Protocol):
    pass


class CreateBreadCommand(Command, Protocol):
    pass


class PublishBreadNotificationCommand(Command, Protocol):
    pass


class CreateWheatBreadCommand:

    def __init__(self, baking_service: BakingService):
        self.__baking_service = baking_service

    def run(self, context: ApplicationContext) -> None:
        self.__baking_service.do_stuff()


class PublishWheatBreadNotificationCommand:

    def __init__(self, baking_service: BakingService):
        self.__baking_service = baking_service

    def run(self, context: ApplicationContext) -> None:
        self.__baking_service.do_stuff()


class CreateWheatBreadSequenceBuilder(FluentSequenceBuilder):

    def __init__(self, create_bread_command: CreateBreadCommand,
                 publish_bread_notification: PublishBreadNotificationCommand):
        super().__init__()
        self.__publish_bread_notification = publish_bread_notification
        self.__create_bread_command = create_bread_command

    def build(self):
        self._add_command(command=self.__create_bread_command).\
            _add_command(command=self.__publish_bread_notification)


class CreateBreadRequestHandler(RequestHandlerBase):

    def __init__(self, sequence: CreateBreadSequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        super().__init__("POST /bake-bread",
                         sequence,
                         command_pipeline,
                         deserializer)


class CreateBreadRequestHandlerInternal(RequestHandlerBase):

    def __init__(self, sequence: CreateBreadSequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        super().__init__("POST /bread",
                         sequence,
                         command_pipeline,
                         deserializer)

handler(event={
    "routeKey": "POST /bake-bread"
}, context={})