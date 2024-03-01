import inspect
from abc import ABC, abstractmethod

from formula_thoughts_web.abstractions import Logger, SequenceComponent, Command, SequenceBuilder, ApplicationContext, Error, \
    ErrorHandlingStrategy
from formula_thoughts_web.exceptions import StrategyNotFoundException

SUBSEQUENCE = "subsequence"
COMMAND = "command"


USE_RESPONSE_ERROR = "USE_RESPONSE_ERROR"
USE_EXCEPTION_ERROR = "USE_EXCEPTION_ERROR"


class FluentSequenceBuilder(ABC):

    def __init__(self):
        self.__components: list[(str, SequenceComponent)] = []

    def _add_command(self, command: Command) -> 'FluentSequenceBuilder':
        self.__components.append((COMMAND, command))
        return self

    def _add_sequence_builder(self, sequence_builder: SequenceBuilder) -> 'FluentSequenceBuilder':
        self.__components.append((SUBSEQUENCE, sequence_builder))
        return self

    def generate_sequence(self) -> list[Command]:
        self.build()
        new_list = []
        for (name, component) in self.__components:
            if name == COMMAND:
                new_list.append(component)
            if name == SUBSEQUENCE:
                sequence_component: SequenceBuilder = component
                commands = sequence_component.generate_sequence()
                new_list.extend(commands)
        return new_list

    @abstractmethod
    def build(self):
        ...

    @property
    def components(self) -> list[SequenceComponent]:
        return list(map(lambda x: x[1], self.__components))


class ErrorHandlingTypeState:

    def __init__(self, default_error_handling_strategy: str):
        self.__error_handling_type: str = default_error_handling_strategy

    @property
    def error_handling_type(self) -> str:
        return self.__error_handling_type

    @error_handling_type.setter
    def error_handling_type(self, value: str) -> None:
        self.__error_handling_type = value


class ExceptionErrorHandlingStrategy:

    def handle_error(self, context: ApplicationContext, error: Error) -> None:
        raise Exception(error.message)

    @property
    def strategy(self) -> str:
        return USE_EXCEPTION_ERROR


class ResponseErrorHandlingStrategy:

    def handle_error(self, context: ApplicationContext, error: Error) -> None:
        context.response = error

    @property
    def strategy(self) -> str:
        return USE_RESPONSE_ERROR


class ErrorHandlingStrategyFactory:

    def __init__(self, error_handling_strategies: list[ErrorHandlingStrategy],
                 error_handling_type_state: ErrorHandlingTypeState) -> None:
        self.__error_handling_type_state = error_handling_type_state
        self.__error_handling_strategies = error_handling_strategies

    def get_error_handling_strategy(self) -> ErrorHandlingStrategy:
        matching_strategies = list(filter(lambda x: x.strategy == self.__error_handling_type_state.error_handling_type, self.__error_handling_strategies))
        if len(matching_strategies) == 0:
            raise StrategyNotFoundException(f"{self.__error_handling_type_state.error_handling_type} not found")

        return matching_strategies[0]


class TopLevelSequenceRunner:

    def __init__(self, error_handling_strategy_factory: ErrorHandlingStrategyFactory, logger: Logger):
        self.__error_handling_strategy_factory = error_handling_strategy_factory
        self.__logger = logger

    def run(self, context: ApplicationContext,
            top_level_sequence: SequenceBuilder):
        commands = top_level_sequence.generate_sequence()
        for command in commands:
            name = "anonymous"
            try:
                name = f"{type(command).__module__}.{type(command).__name__}"
            except Exception:
                ...
            try:
                self.__logger.log_event(message="command event", properties={"action": name})
                self.__logger.log_info(f"begin command {name}")
                self.__logger.log_trace(f"request {context.body}")
                self.__logger.log_trace(f"response {context.response}")
                command.run(context)
                # for now, we throw on first error in top level sequence
                if any(context.error_capsules):
                    error = context.error_capsules[-1]
                    self.__logger.log_error(f"error found in error capsule {type(error).__name__}")
                    self.__error_handling_strategy_factory.get_error_handling_strategy().handle_error(context=context,
                                                                                                      error=error)
                    self.__logger.log_error(f"command pipeline SHORTED!")
                    break
            except Exception as e:
                self.__logger.log_error(f"command pipeline SHORTED due to an exception!")
                raise e
            finally:
                self.__logger.log_info(f"end command {name}")


