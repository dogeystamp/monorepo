from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import AsyncIterator, Iterator


class StatusCode(Enum):
    """
    Status codes for an individual test case.
    """

    AC = auto()
    """
    All Correct: output was valid.
    """
    WA = auto()
    """
    Wrong Answer: output was wrong.
    """
    TLE = auto()
    """
    Time Limit Exceeded: program took too long to execute this case.
    """
    IR = auto()
    """
    Invalid Return: program did not return 0
    """


class TestInput(ABC):
    """Input provider for single test case."""

    @abstractmethod
    async def get_input(self) -> str:
        pass


class TestValidator(ABC):
    """Output validator for single test case."""

    @abstractmethod
    async def validate_output(self, output: str) -> bool:
        pass


@dataclass
class TestOptions:
    """
    Options for running a test suite.

    Attributes
    ----------

    time_limit
        Time limit in seconds for each test case.
    """

    time_limit: float


class TestData(TestInput, TestValidator):
    """
    All information for a single test case.

    name
        Short name for the test case. Can be a file name.
    """

    name: str


class TestSuite(ABC):
    """Loader for multiple test cases."""

    @abstractmethod
    def __iter__(self) -> Iterator[TestData]:
        pass


@dataclass
class TestStatus:
    """
    Status of an individual test case.
    """

    code: StatusCode

    test_data: TestData

    stderr: str
    stdout: str


class TestRunner(ABC):
    """Runner for test cases."""

    @abstractmethod
    async def run_test(self, data: TestData, opts: TestOptions) -> TestStatus:
        pass

    async def run_test_suite(
        self, data: TestSuite, opts: TestOptions
    ) -> AsyncIterator[TestStatus]:
        for test_case in data:
            yield await self.run_test(test_case, opts)
