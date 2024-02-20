from typing import Protocol

from simple_injection import ServiceCollection

from src.abstractions import Command, ApplicationContext, Logger, SequenceBuilder
from src.application import FluentSequenceBuilder, CommandPipeline
from src.web import RequestHandlerBase


def register_dependencies():
    ioc = ServiceCollection()
    ioc.add_singleton(BakingService)
    ioc.add_singleton(CreateBreadCommand, CreateWheatBreadCommand)
    ioc.add_singleton(PublishBreadNotificationCommand, PublishWheatBreadNotificationCommand)
    ioc.add_singleton(CreateBreadSequenceBuilder, CreateWheatBreadSequenceBuilder)


def handler(event, context):
    register_dependencies()


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

    def __init__(self, sequence: CreateWheatBreadSequenceBuilder, command_pipeline: CommandPipeline):
        super().__init__("POST /bake-bread", sequence, command_pipeline)