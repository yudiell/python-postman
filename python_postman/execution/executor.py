"""
Main execution engine for HTTP requests.

This module contains the RequestExecutor class, which orchestrates the execution
of HTTP requests from Postman collections, including variable resolution,
authentication, script execution, and response handling.
"""

import warnings
import time
from typing import Optional, Dict, Any, Union, TYPE_CHECKING
from .context import ExecutionContext
from .extensions import RequestExtensions
from .variable_resolver import VariableResolver
from .auth_handler import AuthHandler
from .script_runner import ScriptRunner
from .response import ExecutionResponse
from .results import ExecutionResult, CollectionExecutionResult, FolderExecutionResult
from .exceptions import ExecutionError, RequestExecutionError
from ..models.request import Request
from ..models.collection import Collection
from ..models.folder import Folder

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

# Type annotations for when httpx is not available
if TYPE_CHECKING and not HTTPX_AVAILABLE:
    import httpx


class RequestExecutor:
    """
    Main class for executing HTTP requests from Postman collections.

    The RequestExecutor orchestrates the complete request execution flow,
    including variable resolution, authentication, pre-request scripts,
    HTTP request execution, and test script execution.

    Examples:
        Basic usage:

        >>> import asyncio
        >>> from python_postman import PythonPostman
        >>> from python_postman.execution import RequestExecutor, ExecutionContext
        >>>
        >>> async def main():
        ...     # Load collection
        ...     collection = PythonPostman.from_file("api_collection.json")
        ...
        ...     # Create executor
        ...     executor = RequestExecutor(
        ...         client_config={"timeout": 30.0, "verify": True},
        ...         global_headers={"User-Agent": "python-postman/1.0"}
        ...     )
        ...
        ...     # Execute single request
        ...     request = collection.get_request_by_name("Get Users")
        ...     context = ExecutionContext(
        ...         environment_variables={"base_url": "https://api.example.com"}
        ...     )
        ...
        ...     result = await executor.execute_request(request, context)
        ...     if result.success:
        ...         print(f"Status: {result.response.status_code}")
        ...         print(f"Response: {result.response.text}")
        ...
        ...     await executor.aclose()
        >>>
        >>> asyncio.run(main())

        Using as context manager:

        >>> async def main():
        ...     async with RequestExecutor() as executor:
        ...         # executor will be automatically closed
        ...         result = await executor.execute_request(request, context)
        >>>
        >>> asyncio.run(main())

        Synchronous execution:

        >>> with RequestExecutor() as executor:
        ...     result = executor.execute_request_sync(request, context)
        ...     print(f"Status: {result.response.status_code}")
    """

    def __init__(
        self,
        client_config: Optional[Dict[str, Any]] = None,
        variable_overrides: Optional[Dict[str, Any]] = None,
        global_headers: Optional[Dict[str, str]] = None,
        script_timeout: float = 30.0,
        request_delay: float = 0.0,
    ):
        """
        Initialize the executor with configuration options.

        Args:
            client_config: Configuration options for the httpx client
            variable_overrides: Global variable overrides
            global_headers: Headers to add to all requests
            script_timeout: Timeout for script execution in seconds
            request_delay: Delay between requests in seconds

        Raises:
            ExecutionError: If httpx is not available
        """
        if not HTTPX_AVAILABLE:
            raise ExecutionError(
                "httpx is required for request execution. Install with: pip install httpx"
            )

        # Store configuration
        self.variable_overrides = variable_overrides or {}
        self.global_headers = global_headers or {}
        self.script_timeout = script_timeout
        self.request_delay = request_delay

        # Set up default client configuration
        default_config = {
            "timeout": 30.0,
            "verify": True,
            "follow_redirects": True,
        }

        # Merge user config with defaults
        self.client_config = {**default_config, **(client_config or {})}

        # Warn about insecure SSL settings
        if not self.client_config.get("verify", True):
            warnings.warn(
                "SSL verification is disabled. This is insecure and should only be used for testing.",
                UserWarning,
                stacklevel=2,
            )

        # Initialize helper components
        self.auth_handler = AuthHandler()

        # HTTP clients will be created lazily
        self._sync_client: Optional["httpx.Client"] = None
        self._async_client: Optional["httpx.AsyncClient"] = None

    def _get_sync_client(self) -> "httpx.Client":
        """Get or create the synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(**self.client_config)
        return self._sync_client

    def _get_async_client(self) -> "httpx.AsyncClient":
        """Get or create the asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(**self.client_config)
        return self._async_client

    def _create_execution_context(
        self,
        collection: Optional[Collection] = None,
        folder: Optional[Folder] = None,
        request: Optional[Request] = None,
        additional_variables: Optional[Dict[str, Any]] = None,
    ) -> ExecutionContext:
        """
        Create an execution context with proper variable scoping.

        Args:
            collection: Collection containing variables
            folder: Folder containing variables
            request: Request containing variables
            additional_variables: Additional variables to include

        Returns:
            ExecutionContext: Configured execution context
        """
        # Extract variables from collection
        collection_vars = {}
        if collection and hasattr(collection, "variable") and collection.variable:
            for var in collection.variable:
                if hasattr(var, "key") and hasattr(var, "value"):
                    collection_vars[var.key] = var.value

        # Extract variables from folder
        folder_vars = {}
        if folder and hasattr(folder, "variable") and folder.variable:
            for var in folder.variable:
                if hasattr(var, "key") and hasattr(var, "value"):
                    folder_vars[var.key] = var.value

        # Extract variables from request
        request_vars = {}
        if request and hasattr(request, "variable") and request.variable:
            for var in request.variable:
                if hasattr(var, "key") and hasattr(var, "value"):
                    request_vars[var.key] = var.value

        # Merge with overrides and additional variables
        environment_vars = {**self.variable_overrides, **(additional_variables or {})}

        context = ExecutionContext(
            collection_variables=collection_vars,
            folder_variables=folder_vars,
            environment_variables=environment_vars,
            request_variables=request_vars,
        )

        # Store collection reference for auth inheritance
        if collection:
            context._collection = collection

        return context

    def _prepare_request(
        self,
        request: Request,
        context: ExecutionContext,
        substitutions: Optional[Dict[str, Any]] = None,
        extensions: Optional[RequestExtensions] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a request for execution by resolving variables, applying auth, and extensions.

        Args:
            request: The request to prepare
            context: Execution context with variables
            substitutions: Runtime variable substitutions
            extensions: Runtime request extensions

        Returns:
            Dictionary containing prepared request parameters for httpx

        Raises:
            RequestExecutionError: If request preparation fails
        """
        try:
            # Create a child context with substitutions
            if substitutions:
                child_context = ExecutionContext(
                    collection_variables=context.collection_variables,
                    folder_variables=context.folder_variables,
                    environment_variables={
                        **context.environment_variables,
                        **substitutions,
                    },
                    request_variables=context.request_variables,
                )
            else:
                child_context = context

            # Apply extensions to create modified request if needed
            working_request = request
            if extensions:
                working_request = extensions.apply_to_request(request, child_context)

            # Initialize variable resolver
            resolver = VariableResolver(child_context)

            # Resolve URL
            url = (
                resolver.resolve_url(working_request.url) if working_request.url else ""
            )
            if not url:
                raise RequestExecutionError("Request URL is required")

            # Resolve headers
            headers = resolver.resolve_headers(working_request.headers or [])

            # Add global headers
            headers.update(self.global_headers)

            # Resolve and apply authentication
            collection_auth = None
            if hasattr(working_request, "_collection") and working_request._collection:
                collection_auth = getattr(working_request._collection, "auth", None)

            auth_data = self.auth_handler.apply_auth(
                working_request.auth, collection_auth, child_context
            )

            # Merge auth headers
            if auth_data.get("headers"):
                headers.update(auth_data["headers"])

            # Resolve body
            body = (
                resolver.resolve_body(working_request.body)
                if working_request.body
                else None
            )

            # Prepare httpx request parameters
            request_params = {
                "method": (
                    working_request.method.upper() if working_request.method else "GET"
                ),
                "url": url,
                "headers": headers,
            }

            # Add body if present
            if body is not None:
                if isinstance(body, dict):
                    request_params["json"] = body
                elif isinstance(body, str):
                    request_params["content"] = body
                else:
                    request_params["content"] = body

            # Add query parameters from auth if present
            if auth_data.get("params"):
                request_params["params"] = auth_data["params"]

            return request_params

        except Exception as e:
            if isinstance(e, RequestExecutionError):
                raise
            raise RequestExecutionError(f"Failed to prepare request: {str(e)}") from e

    def close(self) -> None:
        """Close HTTP clients and clean up resources."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            # Note: async client close should be awaited, but we can't do that in sync method
            # Users should call aclose() for proper async cleanup
            self._async_client = None

    async def aclose(self) -> None:
        """Close HTTP clients asynchronously and clean up resources."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()

    async def execute_request(
        self,
        request: Request,
        context: ExecutionContext,
        substitutions: Optional[Dict[str, Any]] = None,
        extensions: Optional[RequestExtensions] = None,
    ) -> ExecutionResult:
        """
        Execute a single request asynchronously.

        Args:
            request: The request to execute
            context: Execution context with variables and state
            substitutions: Runtime variable substitutions
            extensions: Runtime request extensions

        Returns:
            ExecutionResult: Result of the request execution

        Examples:
            Basic request execution:

            >>> result = await executor.execute_request(request, context)
            >>> if result.success:
            ...     print(f"Success: {result.response.status_code}")
            ... else:
            ...     print(f"Error: {result.error}")

            With runtime substitutions:

            >>> substitutions = {
            ...     "user_id": "12345",
            ...     "api_key": "secret-key"
            ... }
            >>> result = await executor.execute_request(
            ...     request, context, substitutions=substitutions
            ... )

            With request extensions:

            >>> from python_postman.execution import RequestExtensions
            >>> extensions = RequestExtensions(
            ...     header_extensions={"X-Request-ID": "req-123"},
            ...     param_extensions={"debug": "true"}
            ... )
            >>> result = await executor.execute_request(
            ...     request, context, extensions=extensions
            ... )
        """
        execution_start = time.time()
        response = None
        error = None
        test_results = None

        try:
            # Initialize script runner
            script_runner = ScriptRunner(timeout=self.script_timeout)

            # Execute pre-request scripts
            collection = getattr(request, "_collection", None)
            script_runner.execute_pre_request_scripts(request, collection, context)

            # Prepare the HTTP request
            request_params = self._prepare_request(
                request, context, substitutions, extensions
            )

            # Execute the HTTP request asynchronously
            client = self._get_async_client()

            # Add delay if configured
            if self.request_delay > 0:
                import asyncio

                await asyncio.sleep(self.request_delay)

            request_start = time.time()
            httpx_response = await client.request(**request_params)
            request_end = time.time()

            # Wrap response
            response = ExecutionResponse(httpx_response, request_start, request_end)

            # Execute test scripts
            test_results = script_runner.execute_test_scripts(
                request, response, context
            )

        except Exception as e:
            error = e
            if isinstance(e, RequestExecutionError):
                # Re-raise execution errors as-is
                pass
            else:
                # Wrap other exceptions
                error = RequestExecutionError(f"Request execution failed: {str(e)}")

        execution_end = time.time()
        execution_time_ms = (execution_end - execution_start) * 1000

        # Create and return execution result
        return ExecutionResult(
            request=request,
            response=response,
            error=error,
            test_results=test_results,
            execution_time_ms=execution_time_ms,
        )

    def execute_request_sync(
        self,
        request: Request,
        context: ExecutionContext,
        substitutions: Optional[Dict[str, Any]] = None,
        extensions: Optional[RequestExtensions] = None,
    ) -> ExecutionResult:
        """
        Execute a single request synchronously.

        Args:
            request: The request to execute
            context: Execution context with variables and state
            substitutions: Runtime variable substitutions
            extensions: Runtime request extensions

        Returns:
            ExecutionResult: Result of the request execution
        """
        execution_start = time.time()
        response = None
        error = None
        test_results = None

        try:
            # Initialize script runner
            script_runner = ScriptRunner(timeout=self.script_timeout)

            # Execute pre-request scripts
            collection = getattr(request, "_collection", None)
            script_runner.execute_pre_request_scripts(request, collection, context)

            # Prepare the HTTP request
            request_params = self._prepare_request(
                request, context, substitutions, extensions
            )

            # Execute the HTTP request
            client = self._get_sync_client()

            # Add delay if configured
            if self.request_delay > 0:
                time.sleep(self.request_delay)

            request_start = time.time()
            httpx_response = client.request(**request_params)
            request_end = time.time()

            # Wrap response
            response = ExecutionResponse(httpx_response, request_start, request_end)

            # Execute test scripts
            test_results = script_runner.execute_test_scripts(
                request, response, context
            )

        except Exception as e:
            error = e
            if isinstance(e, RequestExecutionError):
                # Re-raise execution errors as-is
                pass
            else:
                # Wrap other exceptions
                error = RequestExecutionError(f"Request execution failed: {str(e)}")

        execution_end = time.time()
        execution_time_ms = (execution_end - execution_start) * 1000

        # Create and return execution result
        return ExecutionResult(
            request=request,
            response=response,
            error=error,
            test_results=test_results,
            execution_time_ms=execution_time_ms,
        )

    async def execute_collection(
        self,
        collection: Collection,
        parallel: bool = False,
        stop_on_error: bool = False,
    ) -> CollectionExecutionResult:
        """
        Execute all requests in a collection.

        Args:
            collection: The collection to execute
            parallel: Whether to execute requests in parallel
            stop_on_error: Whether to stop execution on first error

        Returns:
            CollectionExecutionResult: Result of the collection execution

        Examples:
            Sequential execution:

            >>> result = await executor.execute_collection(collection)
            >>> print(f"Executed {result.total_requests} requests")
            >>> print(f"Success rate: {result.successful_requests}/{result.total_requests}")

            Parallel execution:

            >>> result = await executor.execute_collection(
            ...     collection, parallel=True
            ... )
            >>> print(f"Parallel execution completed in {result.total_time_ms}ms")

            Stop on first error:

            >>> result = await executor.execute_collection(
            ...     collection, stop_on_error=True
            ... )
            >>> if result.failed_requests > 0:
            ...     print("Execution stopped due to error")
        """
        import asyncio

        execution_start = time.time()

        # Create collection execution result
        result = CollectionExecutionResult(
            collection_name=(
                collection.info.name if collection.info else "Unknown Collection"
            )
        )

        # Create execution context for the collection
        context = self._create_execution_context(collection=collection)

        # Get all requests from the collection
        all_requests = list(collection.get_all_requests())

        # Set collection reference on requests for auth inheritance
        for request in all_requests:
            request._collection = collection

        if parallel:
            # Execute requests in parallel
            if all_requests:
                # Create tasks for all requests
                tasks = []
                for request in all_requests:
                    task = asyncio.create_task(self.execute_request(request, context))
                    tasks.append(task)

                # Wait for all tasks to complete
                execution_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and handle exceptions
                for i, exec_result in enumerate(execution_results):
                    if isinstance(exec_result, Exception):
                        # Create failed execution result for exceptions
                        failed_result = ExecutionResult(
                            request=all_requests[i],
                            error=exec_result,
                            execution_time_ms=0.0,
                        )
                        result.add_result(failed_result)

                        if stop_on_error:
                            break
                    else:
                        result.add_result(exec_result)

                        if stop_on_error and not exec_result.success:
                            break
        else:
            # Execute requests sequentially
            for request in all_requests:
                try:
                    exec_result = await self.execute_request(request, context)
                    result.add_result(exec_result)

                    # Stop on error if configured
                    if stop_on_error and not exec_result.success:
                        break

                except Exception as e:
                    # Create failed execution result for exceptions
                    failed_result = ExecutionResult(
                        request=request, error=e, execution_time_ms=0.0
                    )
                    result.add_result(failed_result)

                    if stop_on_error:
                        break

        # Calculate total execution time
        execution_end = time.time()
        result.total_time_ms = (execution_end - execution_start) * 1000

        return result

    async def execute_folder(
        self,
        folder: Folder,
        context: ExecutionContext,
        parallel: bool = False,
        stop_on_error: bool = False,
    ) -> FolderExecutionResult:
        """
        Execute all requests in a folder.

        Args:
            folder: The folder to execute
            context: Execution context with variables and state
            parallel: Whether to execute requests in parallel
            stop_on_error: Whether to stop execution on first error

        Returns:
            FolderExecutionResult: Result of the folder execution
        """
        import asyncio

        execution_start = time.time()

        # Create folder execution result
        result = FolderExecutionResult(folder_name=folder.name)

        # Create child context with folder variables
        folder_context = self._create_execution_context(
            collection=getattr(context, "_collection", None),
            folder=folder,
            additional_variables=context.environment_variables,
        )

        # Merge parent context variables with folder context
        if hasattr(context, "collection_variables"):
            folder_context.collection_variables.update(context.collection_variables)
        if hasattr(context, "environment_variables"):
            folder_context.environment_variables.update(context.environment_variables)

        # Get all requests from the folder (including nested folders)
        all_requests = list(folder.get_requests())

        # Set collection reference on requests for auth inheritance
        collection = getattr(context, "_collection", None)
        for request in all_requests:
            if not hasattr(request, "_collection") or request._collection is None:
                request._collection = collection

        if parallel:
            # Execute requests in parallel
            if all_requests:
                # Create tasks for all requests
                tasks = []
                for request in all_requests:
                    task = asyncio.create_task(
                        self.execute_request(request, folder_context)
                    )
                    tasks.append(task)

                # Wait for all tasks to complete
                execution_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and handle exceptions
                for i, exec_result in enumerate(execution_results):
                    if isinstance(exec_result, Exception):
                        # Create failed execution result for exceptions
                        failed_result = ExecutionResult(
                            request=all_requests[i],
                            error=exec_result,
                            execution_time_ms=0.0,
                        )
                        result.add_result(failed_result)

                        if stop_on_error:
                            break
                    else:
                        result.add_result(exec_result)

                        if stop_on_error and not exec_result.success:
                            break
        else:
            # Execute requests sequentially
            for request in all_requests:
                try:
                    exec_result = await self.execute_request(request, folder_context)
                    result.add_result(exec_result)

                    # Stop on error if configured
                    if stop_on_error and not exec_result.success:
                        break

                except Exception as e:
                    # Create failed execution result for exceptions
                    failed_result = ExecutionResult(
                        request=request, error=e, execution_time_ms=0.0
                    )
                    result.add_result(failed_result)

                    if stop_on_error:
                        break

        # Calculate total execution time
        execution_end = time.time()
        result.total_time_ms = (execution_end - execution_start) * 1000

        return result
