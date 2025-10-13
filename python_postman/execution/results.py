"""
Result classes for execution operations.

This module defines the data structures used to represent the results of
request execution, including individual request results, test results,
and collection execution results.
"""

from typing import List, Optional, Any, Dict
from dataclasses import dataclass, field
from ..models.request import Request


@dataclass
class ScriptAssertion:
    """
    Individual test assertion result.

    Represents the result of a single assertion within a test script,
    including whether it passed and any error information.
    """

    name: str
    passed: bool
    error: Optional[str] = None

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        if self.error and not self.passed:
            return f"{status}: {self.name} - {self.error}"
        return f"{status}: {self.name}"


@dataclass
class ScriptResults:
    """
    Results from test script execution.

    Aggregates all test assertions and provides summary statistics
    for test execution results.
    """

    passed: int = 0
    failed: int = 0
    assertions: List[ScriptAssertion] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total number of test assertions."""
        return self.passed + self.failed

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage (0.0 to 1.0)."""
        if self.total == 0:
            return 1.0
        return self.passed / self.total

    def add_assertion(self, assertion: ScriptAssertion) -> None:
        """
        Add a test assertion result.

        Args:
            assertion: The test assertion result to add
        """
        self.assertions.append(assertion)
        if assertion.passed:
            self.passed += 1
        else:
            self.failed += 1

    def __str__(self) -> str:
        return f"Tests: {self.passed} passed, {self.failed} failed, {self.total} total"


@dataclass
class ExecutionResult:
    """
    Result of executing a single request.

    Contains the request that was executed, the response (if successful),
    any error that occurred, test results, and timing information.
    """

    request: Request
    response: Optional["ExecutionResponse"] = None
    error: Optional[Exception] = None
    test_results: Optional[ScriptResults] = None
    execution_time_ms: float = 0.0

    @property
    def success(self) -> bool:
        """Whether the request execution was successful."""
        return self.error is None and self.response is not None

    @property
    def status_code(self) -> Optional[int]:
        """HTTP status code if response is available."""
        return self.response.status_code if self.response else None

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        time_str = f"{self.execution_time_ms:.2f}ms"

        if self.success and self.response:
            return f"{status}: {self.request.name} ({self.response.status_code}) - {time_str}"
        elif self.error:
            return f"{status}: {self.request.name} - {str(self.error)} - {time_str}"
        else:
            return f"{status}: {self.request.name} - {time_str}"


@dataclass
class FolderExecutionResult:
    """
    Result of executing all requests in a folder.

    Contains execution results for all requests in the folder,
    along with summary statistics and timing information.
    """

    folder_name: str
    results: List[ExecutionResult] = field(default_factory=list)
    total_time_ms: float = 0.0

    @property
    def total_requests(self) -> int:
        """Total number of requests executed."""
        return len(self.results)

    @property
    def successful_requests(self) -> int:
        """Number of successful requests."""
        return sum(1 for result in self.results if result.success)

    @property
    def failed_requests(self) -> int:
        """Number of failed requests."""
        return self.total_requests - self.successful_requests

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def test_results(self) -> ScriptResults:
        """Aggregated test results from all requests."""
        aggregated = ScriptResults()
        for result in self.results:
            if result.test_results:
                aggregated.passed += result.test_results.passed
                aggregated.failed += result.test_results.failed
                aggregated.assertions.extend(result.test_results.assertions)
        return aggregated

    def add_result(self, result: ExecutionResult) -> None:
        """
        Add a request execution result.

        Args:
            result: The execution result to add
        """
        self.results.append(result)
        self.total_time_ms += result.execution_time_ms

    def __str__(self) -> str:
        time_str = f"{self.total_time_ms:.2f}ms"
        return (
            f"Folder '{self.folder_name}': {self.successful_requests}/{self.total_requests} "
            f"requests successful - {time_str}"
        )


@dataclass
class CollectionExecutionResult:
    """
    Result of executing an entire collection.

    Contains execution results for all requests in the collection,
    organized by folders, along with summary statistics and timing information.
    """

    collection_name: str
    results: List[ExecutionResult] = field(default_factory=list)
    folder_results: List[FolderExecutionResult] = field(default_factory=list)
    total_time_ms: float = 0.0

    @property
    def total_requests(self) -> int:
        """Total number of requests executed."""
        return len(self.results)

    @property
    def successful_requests(self) -> int:
        """Number of successful requests."""
        return sum(1 for result in self.results if result.success)

    @property
    def failed_requests(self) -> int:
        """Number of failed requests."""
        return self.total_requests - self.successful_requests

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def test_results(self) -> ScriptResults:
        """Aggregated test results from all requests."""
        aggregated = ScriptResults()
        for result in self.results:
            if result.test_results:
                aggregated.passed += result.test_results.passed
                aggregated.failed += result.test_results.failed
                aggregated.assertions.extend(result.test_results.assertions)
        return aggregated

    def add_result(self, result: ExecutionResult) -> None:
        """
        Add a request execution result.

        Args:
            result: The execution result to add
        """
        self.results.append(result)
        self.total_time_ms += result.execution_time_ms

    def add_folder_result(self, folder_result: FolderExecutionResult) -> None:
        """
        Add a folder execution result.

        Args:
            folder_result: The folder execution result to add
        """
        self.folder_results.append(folder_result)
        self.results.extend(folder_result.results)
        self.total_time_ms += folder_result.total_time_ms

    def __str__(self) -> str:
        time_str = f"{self.total_time_ms:.2f}ms"
        return (
            f"Collection '{self.collection_name}': {self.successful_requests}/{self.total_requests} "
            f"requests successful - {time_str}"
        )
