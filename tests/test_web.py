from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from callee import Captor, Any

from src.abstractions import SequenceBuilder, ApplicationContext, RequestHandler, Deserializer
from src.application import TopLevelSequenceRunner
from src.crosscutting import JsonSnakeToCamelSerializer, JsonCamelToSnakeDeserializer
from src.web import ApiRequestHandlerBase, WebRunner, StatusCodeMapping


class ExampleRequestHandler(ApiRequestHandlerBase):

    def __init__(self, mock_sequence: SequenceBuilder,
                 command_pipeline: TopLevelSequenceRunner,
                 deserializer: Deserializer):
        super().__init__("GET /test/route",
                         mock_sequence,
                         command_pipeline,
                         deserializer)


class TestRequestHandler(TestCase):

    def setUp(self):
        self.__mock_sequence: SequenceBuilder = Mock()
        self.__mock_pipeline: TopLevelSequenceRunner = Mock()
        self.__sut = ExampleRequestHandler(mock_sequence=self.__mock_sequence,
                                           command_pipeline=self.__mock_pipeline,
                                           deserializer=JsonCamelToSnakeDeserializer())

    def test_handle_basic_request(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.run = MagicMock()
        event = {}

        # act
        context = self.__sut.run(event=event)

        context_captor = Captor()

        # assert
        with self.subTest(msg="assert pipeline was called once"):
            self.__mock_pipeline.run.assert_called_once()

        # assert
        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.run.assert_called_with(context=context_captor,
                                                        top_level_sequence=self.__mock_sequence)

        # assert
        with self.subTest(msg="assert context was built correctly"):
            captured_context: ApplicationContext = context_captor.arg
            self.assertEqual(captured_context.body, None)
            self.assertEqual(captured_context.auth_user_id, None)
            self.assertEqual(captured_context.parameters, {})
            self.assertEqual(captured_context.error_capsules, [])

        with self.subTest(msg="assert context was returned"):
            self.assertEqual(context, context_captor.arg)

    def test_handle_request_with_json_body(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.run = MagicMock()
        event = {
            "body": "{\"field1\": \"value1\", \"field2\": 2.45, \"camelCaseField\": \"camelCase\"}"
        }

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.run.assert_called_with(context=context_captor, top_level_sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, {"field_1": "value1", "field_2": 2.45, "camel_case_field": "camelCase"})

    def test_handle_request_with_string_body(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.run = MagicMock()
        event = {
            "body": "this is a test"
        }

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.run.assert_called_with(context=context_captor, top_level_sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, "this is a test")

    def test_handle_request_with_list_body(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.run = MagicMock()
        event = {
            "body": "[\"1\", \"2\", \"3\"]"
        }

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.run.assert_called_with(context=context_captor, top_level_sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, ["1", "2", "3"])

    def test_handle_request_with_auth_id(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.run = MagicMock()
        event = {"requestContext": {"authorizer": {"jwt": {"claims": {"name": "bob132"}}}}}

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.run.assert_called_with(context=context_captor, top_level_sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.auth_user_id, "bob132")

    def test_handle_request_with_path_and_query_params(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.run = MagicMock()
        event = {"pathParameters": {"path_param1": "value1", "path_param2": "value2"}, "queryStringParameters": {"path_param2": "value1", "path_param3": "value1", "path_param4": 4.2}}

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.run.assert_called_with(context=context_captor, top_level_sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.parameters, {"path_param1": "value1", "path_param2": "value1", "path_param3": "value1", "path_param4": 4.2})


@dataclass(unsafe_hash=True)
class TestResponse:
    test_prop: int = None


class TestWebRunner(TestCase):

    def setUp(self):
        self.__mock_handler1: RequestHandler = Mock()
        self.__mock_handler2: RequestHandler = Mock()
        self.__mock_handler3: RequestHandler = Mock()
        self.__status_code_mapping: StatusCodeMapping = Mock()
        self.__sut = WebRunner(request_handlers=[self.__mock_handler1, self.__mock_handler2, self.__mock_handler3],
                               serializer=JsonSnakeToCamelSerializer(),
                               status_code_mappings=self.__status_code_mapping,
                               logger=Mock())

    def test_run_basic(self):
        # arrange
        event = {
            "routeKey": "GET /test/path1",
            "body": "{\"testField\": \"testValue\"}"
        }
        context = ApplicationContext(response=TestResponse(test_prop=1))
        self.__mock_handler1.run = MagicMock(return_value=context)
        self.__mock_handler1.route_key = "GET /test/path1"
        self.__status_code_mapping.get_mappings = MagicMock(return_value=200)

        # act
        response = self.__sut.run(event=event)

        # assert
        with self.subTest(msg="assert correct handler was run"):
            self.__mock_handler1.run.assert_called_once()

        # assert
        with self.subTest(msg="assert correct handler was run with event"):
            self.__mock_handler1.run.assert_called_with(event=event)

        # assert
        with self.subTest(msg="body matches"):
            self.assertEqual(response['body'], "{\"testProp\": 1}")

        with self.subTest(msg="status code matches"):
            self.assertEqual(response['statusCode'], 200)

        with self.subTest(msg="assert headers match"):
            self.assertEqual(response['headers'], {"Content-Type": "application/json"})

    def test_run_without_response(self):
        # arrange
        event = {
            "routeKey": "GET /test/path1",
            "body": "{\"testField\": \"testValue\"}"
        }
        context = ApplicationContext(response=None)
        self.__mock_handler1.run = MagicMock(return_value=context)
        self.__mock_handler1.route_key = "GET /test/path1"

        # act
        response = self.__sut.run(event=event)

        # assert
        with self.subTest(msg="body matches"):
            self.assertEqual(response['body'], None)

        with self.subTest(msg="status code matches"):
            self.assertEqual(response['statusCode'], 204)

    def test_run_basic_with_no_route_match(self):
        # arrange
        event = {
            "routeKey": "POST /test/path1",
            "body": "{\"testField\": \"testValue\"}"
        }
        self.__mock_handler1.run = MagicMock()
        self.__mock_handler1.route_key = "GET /test/path1"

        # act
        response = self.__sut.run(event=event)

        # assert
        with self.subTest(msg="assert correct handler was not run"):
            self.__mock_handler1.run.assert_not_called()

        # assert
        with self.subTest(msg="body matches"):
            self.assertEqual(response['body'], "{\"message\": \"route POST /test/path1 not found\"}")

        with self.subTest(msg="status code matches"):
            self.assertEqual(response['statusCode'], 404)

    def test_run_basic_with_exception(self):
        # arrange
        event = {
            "routeKey": "GET /test/path1",
            "body": "{\"testField\": \"testValue\"}"
        }
        self.__mock_handler1.run = MagicMock(return_value=Exception("test exception"))
        self.__mock_handler1.route_key = "GET /test/path1"

        # act
        response = self.__sut.run(event=event)

        # assert
        with self.subTest(msg="assert correct handler was not run"):
            self.__mock_handler1.run.assert_called_once()

        # assert
        with self.subTest(msg="body matches"):
            self.assertEqual(response['body'], "{\"message\": \"internal server error :(\"}")

        with self.subTest(msg="status code matches"):
            self.assertEqual(response['statusCode'], 500)