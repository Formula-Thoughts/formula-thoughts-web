from unittest import TestCase
from unittest.mock import Mock, MagicMock

from callee import Captor, Any

from src.abstractions import SequenceBuilder, ApplicationContext
from src.application import CommandPipeline
from src.web import RequestHandlerBase


class RequestHandler(RequestHandlerBase):

    def __init__(self, mock_sequence: SequenceBuilder, command_pipeline: CommandPipeline):
        super().__init__("GET /test/route", mock_sequence, command_pipeline)


class TestRequestHandler(TestCase):

    def setUp(self):
        self.__mock_sequence: SequenceBuilder = Mock()
        self.__mock_pipeline: CommandPipeline = Mock()
        self.__sut = RequestHandler(mock_sequence=self.__mock_sequence, command_pipeline=self.__mock_pipeline)

    def test_handle_basic_request(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.execute_commands = MagicMock()
        event = {}

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        # assert
        with self.subTest(msg="assert pipeline was called once"):
            self.__mock_pipeline.execute_commands.assert_called_once()

        # assert
        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.execute_commands.assert_called_with(context=context_captor,
                                                                     sequence=self.__mock_sequence)

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, None)
            self.assertEqual(context.auth_user_id, None)
            self.assertEqual(context.parameters, {})

    def test_handle_request_with_json_body(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.execute_commands = MagicMock()
        event = {
            "body": "{\"field1\": \"value1\", \"field2\": 2.45}"
        }

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.execute_commands.assert_called_with(context=context_captor, sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, {"field1": "value1", "field2": 2.45})

    def test_handle_request_with_string_body(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.execute_commands = MagicMock()
        event = {
            "body": "this is a test"
        }

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.execute_commands.assert_called_with(context=context_captor, sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, "this is a test")

    def test_handle_request_with_list_body(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.execute_commands = MagicMock()
        event = {
            "body": "[\"1\", \"2\", \"3\"]"
        }

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.execute_commands.assert_called_with(context=context_captor, sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.body, ["1", "2", "3"])

    def test_handle_request_with_auth_id(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.execute_commands = MagicMock()
        event = {"requestContext": {"authorizer": {"jwt": {"claims": {"name": "bob132"}}}}}

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.execute_commands.assert_called_with(context=context_captor, sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.auth_user_id, "bob132")

    def test_handle_request_with_path_and_query_params(self):
        # arrange
        self.__mock_sequence.generate_sequence = MagicMock()
        self.__mock_pipeline.execute_commands = MagicMock()
        event = {"pathParameters": {"path_param1": "value1", "path_param2": "value2"}, "queryStringParameters": {"path_param2": "value1", "path_param3": "value1", "path_param4": 4.2}}

        # act
        self.__sut.run(event=event)

        context_captor = Captor()

        with self.subTest(msg="assert pipeline was called was correct context and sequence"):
            self.__mock_pipeline.execute_commands.assert_called_with(context=context_captor, sequence=Any())

        # assert
        with self.subTest(msg="assert context was built correctly"):
            context: ApplicationContext = context_captor.arg
            self.assertEqual(context.parameters, {"path_param1": "value1", "path_param2": "value1", "path_param3": "value1", "path_param4": 4.2})
