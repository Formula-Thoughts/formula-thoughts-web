import json
import uuid
from dataclasses import dataclass
from typing import Protocol
from unittest import TestCase

from src.abstractions import Command, ApplicationContext, Logger, SequenceBuilder, Deserializer, \
    ApiRequestHandler, Error
from src.application import FluentSequenceBuilder, TopLevelSequenceRunner
from src.crosscutting import ObjectMapper
from src.exceptions import MappingException
from src.ioc import register_web, Container
from src.web import ApiRequestHandlerBase, WebRunner

BAKING_ID = str(uuid.uuid4())


BAKING_ID_VAR = "BAKING_ID"
BAKING_REQUEST_VAR = "BAKING_REQUEST"


def register_dependencies(services: Container) -> None:
    services.register(BakingService)
    services.register(NotificationService)
    services.register(CreateBreadRequestCommand, CreateWhiteBreadRequestCommand)
    services.register(ValidateBreadRequestCommand, ValidateWhiteBreadRequestCommand)
    services.register(CreateBreadCommand, CreateWhiteBreadCommand)
    services.register(PublishBreadNotificationCommand, PublishWhiteBreadNotificationCommand)
    services.register(CreateBreadSequenceBuilder, CreateWhiteBreadSequenceBuilder)
    services.register(ApiRequestHandler, CreateBreadRequestHandler)
    services.register_status_code_mappings({
        BreadResponse: 200,
        BreadValidationError: 400
    })


def handler(event, context) -> dict:
    ioc = Container()
    register_web(services=ioc)
    register_dependencies(services=ioc)
    web_runner = ioc.resolve(service=WebRunner)
    return web_runner.run(event=event)


@dataclass(unsafe_hash=True)
class BreadModel:
    temperature: float = None
    yeast_g: float = None
    flour_g: float = None
    water_ml: float = None
    olive_oil_ml: float = None


@dataclass(unsafe_hash=True)
class BreadNotification:
    temperature: float = None
    baking_id: str = None


class BakingService:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def bake_bread(self, bread: BreadModel) -> str:
        self.__logger.log_info(message=f"baking bread at {bread.temperature} degrees")
        return BAKING_ID


class NotificationService:

    def __init__(self, logger: Logger):
        self.__logger = logger

    def publish(self, notif: dict) -> bool:
        self.__logger.log_info(message=f"raising notification {notif}")
        return True


class CreateBreadSequenceBuilder(SequenceBuilder, Protocol):
    pass


class CreateBreadCommand(Command, Protocol):
    pass


class CreateBreadRequestCommand(Command, Protocol):
    pass


class ValidateBreadRequestCommand(Command, Protocol):
    pass


class PublishBreadNotificationCommand(Command, Protocol):
    pass


@dataclass
class BreadResponse:
    baking_id: str = None


class BreadValidationError(Error):
    pass


temperature_error = BreadValidationError(message="temperature has to be above 0c")
bread_mapping_validation_error = BreadValidationError(message="failed to map request")
yeast_error = BreadValidationError(message="yeast must be above 0g")
flour_error = BreadValidationError(message="flour must be above 0g")
water_error = BreadValidationError(message="water must be above 0ml")
oil_error = BreadValidationError(message="oil must be above 0ml")


class CreateWhiteBreadRequestCommand:

    def __init__(self,
                 mapper: ObjectMapper,
                 logger: Logger):
        self.__logger = logger
        self.__mapper = mapper

    def run(self, context: ApplicationContext) -> None:
        try:
            model = self.__mapper.map_from_dict(_from=context.body, to=BreadModel)
            context.set_var(BAKING_REQUEST_VAR, model)
            self.__logger.add_global_properties(properties={
                "temperature": model.temperature,
                "water": model.water_ml,
                "yeast": model.yeast_g,
                "oil": model.olive_oil_ml,
                "flour": model.flour_g
            })
        except MappingException as e:
            context.error_capsules.append(bread_mapping_validation_error)


class ValidateWhiteBreadRequestCommand:

    def run(self, context: ApplicationContext) -> None:
        request = context.get_var(BAKING_REQUEST_VAR, BreadModel)

        if request.temperature <= 0:
            context.error_capsules.append(temperature_error)

        if request.yeast_g <= 0:
            context.error_capsules.append(yeast_error)

        if request.flour_g <= 0:
            context.error_capsules.append(flour_error)

        if request.water_ml <= 0:
            context.error_capsules.append(water_error)

        if request.olive_oil_ml <= 0:
            context.error_capsules.append(oil_error)


class CreateWhiteBreadCommand:

    def __init__(self, baking_service: BakingService):
        self.__baking_service = baking_service

    def run(self, context: ApplicationContext) -> None:
        _id = self.__baking_service.bake_bread(context.get_var(BAKING_REQUEST_VAR, BreadModel))
        context.set_var(BAKING_ID_VAR, _id)
        context.response = BreadResponse(_id)


class PublishWhiteBreadNotificationCommand:

    def __init__(self, notification_service: NotificationService):
        self.__notification_service = notification_service

    def run(self, context: ApplicationContext) -> None:
        published = self.__notification_service.publish(
            notif=BreadNotification(temperature=context.get_var(BAKING_REQUEST_VAR, BreadModel).temperature,
                                    baking_id=context.get_var(BAKING_ID_VAR, str)).__dict__)


class CreateWhiteBreadSequenceBuilder(FluentSequenceBuilder):

    def __init__(self, create_bread_command: CreateBreadCommand,
                 publish_bread_notification: PublishBreadNotificationCommand,
                 create_bread_request: CreateBreadRequestCommand,
                 validate_bread_request: ValidateBreadRequestCommand):
        super().__init__()
        self.__validate_bread_request = validate_bread_request
        self.__create_bread_request = create_bread_request
        self.__publish_bread_notification = publish_bread_notification
        self.__create_bread_command = create_bread_command

    def build(self):
        self._add_command(command=self.__create_bread_request). \
            _add_command(command=self.__create_bread_command). \
            _add_command(command=self.__validate_bread_request). \
            _add_command(command=self.__publish_bread_notification)


class CreateBreadRequestHandler(ApiRequestHandlerBase):

    def __init__(self, sequence: CreateBreadSequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        super().__init__("POST /bake-bread",
                         sequence,
                         command_pipeline,
                         deserializer)


class TestExampleCode(TestCase):
        
    def test_run_handler(self):
        # arrange & act
        response = handler(event={"routeKey": "POST /bake-bread", "body": json.dumps({"temperature": 14.5, "yeast_g": 24.5, "flour_g": 546.4, "water_ml": 0.1, "olive_oil_ml": 0.2})}, context={})
        
        # assert
        with self.subTest(msg="assert response is OK"):
            self.assertEqual(response['statusCode'], 200)

        # assert
        with self.subTest(msg="assert body matches"):
            self.assertEqual(response['body'], "{\"bakingId\": \""+BAKING_ID+"\"}")

    def test_run_handler_when_there_is_error(self):
        # arrange & act
        response = handler(event={"routeKey": "POST /bake-bread", "body": json.dumps(
            {"temperature": 0, "yeast_g": 24.5, "flour_g": 546.4, "water_ml": 0.1, "olive_oil_ml": 0.2})},
                           context={})

        # assert
        with self.subTest(msg="assert response is bad request"):
            self.assertEqual(response['statusCode'], 400)

        # assert
        with self.subTest(msg="assert body matches"):
            self.assertEqual(response['body'], "{\"message\": \"temperature has to be above 0c\"}")
        