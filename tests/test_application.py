from unittest import TestCase
from unittest.mock import Mock, MagicMock

from autofixture import AutoFixture

from src.abstractions import Error, ErrorHandlingStrategy
from src.application import FluentSequenceBuilder, ApplicationContext, TopLevelSequenceRunner, \
    Command, ErrorHandlingStrategyFactory, ErrorHandlingTypeState, ResponseErrorHandlingStrategy, \
    ExceptionErrorHandlingStrategy
from src.exceptions import StrategyNotFoundException
from tests import logger_factory


class Command1(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 1")


class Command2(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 2")


class Command3(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 3")


class Command4(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 4")


class Command5(Command):

    def run(self, context: ApplicationContext):
        context.body["trail"].append("command 5")


class CommandError(Command):

    def run(self, context: ApplicationContext):
        context.error_capsules.append(Error(message="error"))


class DummyNestedErrorSequenceBuilder(FluentSequenceBuilder):

    def __init__(self):
        super().__init__()

    def build(self):
        self._add_command(Command1()) \
            ._add_command(CommandError()) \
            ._add_command(Command3())


class DummyNested2SequenceBuilder(FluentSequenceBuilder):

    def __init__(self):
        super().__init__()

    def build(self):
        self._add_command(Command3()) \
            ._add_command(Command4()) \
            ._add_command(Command5())


class DummyNestedSequenceBuilder(FluentSequenceBuilder):

    def __init__(self, sequence: DummyNested2SequenceBuilder):
        super().__init__()
        self.__sequence = sequence

    def build(self):
        self._add_sequence_builder(self.__sequence)


class DummySequenceBuilder(FluentSequenceBuilder):

    def __init__(self, sequence: DummyNestedSequenceBuilder):
        super().__init__()
        self.__sequence = sequence

    def build(self):
        self._add_command(Command1()) \
            ._add_sequence_builder(self.__sequence) \
            ._add_command(Command2()) \
            ._add_command(Command3())


class TestSequenceBuilder(TestCase):

    def setUp(self):
        self.__error_handling_strategy_factory: ErrorHandlingStrategyFactory = Mock()
        self.__error_handling_strategy: ErrorHandlingStrategy = Mock()
        self.__top_level_sequence_runner = TopLevelSequenceRunner(logger=logger_factory(),
                                                                  error_handling_strategy_factory=self.__error_handling_strategy_factory)

    def test_sequence(self):
        # arrange
        sut = DummyNested2SequenceBuilder()
        self.__error_handling_strategy_factory.get_error_handling_strategy = MagicMock(
            return_value=self.__error_handling_strategy)
        context = ApplicationContext(body={"trail": []})

        # act
        self.__top_level_sequence_runner.run(context=context,
                                             top_level_sequence=sut)

        # assert
        self.assertEqual(context.body["trail"], ["command 3", "command 4", "command 5"])

    def test_sequence_with_short_circuit(self):
        # arrange
        sut = DummyNestedErrorSequenceBuilder()
        self.__error_handling_strategy.handle_error = MagicMock()
        self.__error_handling_strategy_factory.get_error_handling_strategy = MagicMock(
            return_value=self.__error_handling_strategy)
        context = ApplicationContext(body={"trail": []})

        # act
        self.__top_level_sequence_runner.run(context=context,
                                             top_level_sequence=sut)

        # assert
        with self.subTest("invocations match"):
            self.assertEqual(context.body["trail"], ["command 1"])

        # assert
        with self.subTest("error is handled once"):
            self.__error_handling_strategy.handle_error.assert_called_once()

        # assert
        with self.subTest("error is handled with correct args"):
            self.__error_handling_strategy.handle_error.assert_called_with(context=context,
                                                                           error=Error(message="error"))


class TestComplexSequenceBuilder(TestCase):

    def setUp(self) -> None:
        self.__sut = DummySequenceBuilder(sequence=DummyNestedSequenceBuilder(
            sequence=DummyNested2SequenceBuilder()))
        self.__error_handling_strategy: ErrorHandlingStrategy = Mock()
        self.__error_handling_strategy_factory: ErrorHandlingStrategyFactory = Mock()
        self.__top_level_sequence_runner = TopLevelSequenceRunner(logger=logger_factory(),
                                                                  error_handling_strategy_factory=self.__error_handling_strategy_factory)

    def test_build_and_run_sequence(self):
        # arrange
        context = ApplicationContext(body={"trail": []})
        self.__error_handling_strategy_factory.get_error_handling_strategy = MagicMock(
            return_value=self.__error_handling_strategy)

        # act
        self.__top_level_sequence_runner.run(context=context,
                                             top_level_sequence=self.__sut)

        # assert
        with self.subTest(msg="invocations match list"):
            self.assertEqual(context.body["trail"],
                             ["command 1", "command 3", "command 4", "command 5", "command 2", "command 3"])


class TestErrorHandlingStrategyFactory(TestCase):

    def setUp(self):
        self.__error_handling_state: ErrorHandlingTypeState = ErrorHandlingTypeState(default_error_handling_strategy="unknown")
        self.__error_handling_strategy_1: ErrorHandlingStrategy = Mock()
        self.__error_handling_strategy_2: ErrorHandlingStrategy = Mock()
        self.__sut = ErrorHandlingStrategyFactory(error_handling_strategies=[self.__error_handling_strategy_1, self.__error_handling_strategy_2],
                                                  error_handling_type_state=self.__error_handling_state)

    def test_get_strategy_1(self):
        # arrange
        self.__error_handling_strategy_1.strategy = "1"
        self.__error_handling_state.error_handling_type = "1"

        # act
        strategy = self.__sut.get_error_handling_strategy()

        # assert
        with self.subTest(msg="strategy returned is strategy 1"):
            self.assertEqual(strategy, self.__error_handling_strategy_1)

    def test_get_strategy_1_when_there_are_multiple_of_the_same(self):
        # arrange
        self.__error_handling_strategy_1.strategy = "1"
        self.__error_handling_strategy_2.strategy = "1"
        self.__error_handling_state.error_handling_type = "1"

        # act
        strategy = self.__sut.get_error_handling_strategy()

        # assert
        with self.subTest(msg="strategy returned is strategy 1"):
            self.assertEqual(strategy, self.__error_handling_strategy_1)

    def test_get_strategy_3_when_there_are_no_matching_strategies(self):
        # arrange
        self.__error_handling_strategy_1.strategy = "1"
        self.__error_handling_strategy_2.strategy = "2"
        self.__error_handling_state.error_handling_type = "3"

        # act
        sut_call = lambda: self.__sut.get_error_handling_strategy()

        # assert
        with self.subTest(msg="strategy not found exception is thrown"):
            with self.assertRaises(expected_exception=StrategyNotFoundException):
                sut_call()


class TestResponseErrorHandlingStrategy(TestCase):

    def setUp(self):
        self.__sut = ResponseErrorHandlingStrategy()

    def test_handle_error_should_set_response(self):
        # arrange
        error = AutoFixture().create(dto=Error)
        context = ApplicationContext()

        # act
        self.__sut.handle_error(context=context, error=error)

        # assert
        with self.subTest(msg="assert response is set"):
            self.assertEqual(context.response, error)

    def test_strategy_should_return_response_strategy(self):
        # act
        strategy = self.__sut.strategy

        # assert
        with self.subTest(msg="assert response is set"):
            self.assertEqual(strategy, "USE_RESPONSE_ERROR")


class TestExceptionErrorHandlingStrategy(TestCase):

    def setUp(self):
        self.__sut = ExceptionErrorHandlingStrategy()

    def test_handle_error_should_set_response(self):
        # arrange
        error = AutoFixture().create(dto=Error)
        context = ApplicationContext()

        # act
        sut_call = lambda: self.__sut.handle_error(context=context, error=error)

        # assert
        with self.subTest(msg="assert exception is thrown"):
            with self.assertRaises(expected_exception=Exception, msg=error.message):
                sut_call()

    def test_strategy_should_return_response_strategy(self):
        # act
        strategy = self.__sut.strategy

        # assert
        with self.subTest(msg="assert response is set"):
            self.assertEqual(strategy, "USE_EXCEPTION_ERROR")