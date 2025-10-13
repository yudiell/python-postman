"""
Collection statistics and metadata analysis.
"""

import json
import csv
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from collections import Counter
from io import StringIO

if TYPE_CHECKING:
    from ..models.collection import Collection
    from ..models.folder import Folder
    from ..models.item import Item


class CollectionStatistics:
    """
    Provides statistics and metadata about a collection.
    
    This class analyzes a Postman collection and provides various metrics
    including request counts, folder counts, nesting depth, and breakdowns
    by HTTP method and authentication type.
    
    Examples:
        >>> from python_postman import PythonPostman
        >>> parser = PythonPostman()
        >>> collection = parser.parse("my_collection.json")
        >>> 
        >>> # Get statistics
        >>> stats = collection.get_statistics()
        >>> data = stats.collect()
        >>> print(f"Total requests: {data['total_requests']}")
        >>> print(f"Max depth: {data['max_nesting_depth']}")
        >>> 
        >>> # Export to JSON
        >>> json_output = stats.to_json()
        >>> with open("stats.json", "w") as f:
        ...     f.write(json_output)
        >>> 
        >>> # Export to CSV
        >>> csv_output = stats.to_csv()
        >>> with open("stats.csv", "w") as f:
        ...     f.write(csv_output)
    """

    def __init__(self, collection: "Collection"):
        """
        Initialize CollectionStatistics.
        
        Args:
            collection: The collection to analyze
        """
        self.collection = collection
        self._cache: Optional[Dict[str, Any]] = None

    def collect(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Collect all statistics about the collection.
        
        Args:
            use_cache: Whether to use cached results if available (default: True)
        
        Returns:
            Dictionary containing all statistics:
                - total_requests: Total number of requests
                - total_folders: Total number of folders
                - max_nesting_depth: Maximum folder nesting depth
                - requests_by_method: Dict mapping HTTP methods to counts
                - requests_by_auth: Dict mapping auth types to counts
                - avg_requests_per_folder: Average requests per folder
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> data = stats.collect()
            >>> print(f"Collection has {data['total_requests']} requests")
            >>> print(f"Methods: {data['requests_by_method']}")
        """
        if use_cache and self._cache:
            return self._cache

        stats = {
            "total_requests": self.count_requests(),
            "total_folders": self.count_folders(),
            "max_nesting_depth": self.get_max_depth(),
            "requests_by_method": self.count_by_method(),
            "requests_by_auth": self.count_by_auth(),
            "avg_requests_per_folder": self.get_avg_requests_per_folder(),
        }

        if use_cache:
            self._cache = stats

        return stats

    def count_requests(self) -> int:
        """
        Count total requests in the collection.
        
        Returns:
            Total number of requests
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> total = stats.count_requests()
            >>> print(f"Total requests: {total}")
        """
        return sum(1 for _ in self.collection.get_requests())

    def count_folders(self) -> int:
        """
        Count total folders in the collection.
        
        Returns:
            Total number of folders (including nested folders)
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> total = stats.count_folders()
            >>> print(f"Total folders: {total}")
        """
        return self._count_folders_recursive(self.collection.items)

    def _count_folders_recursive(self, items: List["Item"]) -> int:
        """
        Recursively count folders in a list of items.
        
        Args:
            items: List of items to count folders in
        
        Returns:
            Number of folders found
        """
        from ..models.folder import Folder
        
        count = 0
        for item in items:
            if isinstance(item, Folder):
                count += 1
                count += self._count_folders_recursive(item.items)
        return count

    def get_max_depth(self) -> int:
        """
        Calculate maximum nesting depth of folders.
        
        Returns:
            Maximum folder nesting depth (0 if no folders)
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> depth = stats.get_max_depth()
            >>> print(f"Max nesting depth: {depth}")
        """
        return self._get_max_depth_recursive(self.collection.items, 0)

    def _get_max_depth_recursive(self, items: List["Item"], current_depth: int) -> int:
        """
        Recursively calculate maximum depth.
        
        Args:
            items: List of items to analyze
            current_depth: Current depth level
        
        Returns:
            Maximum depth found
        """
        from ..models.folder import Folder
        
        max_depth = current_depth
        for item in items:
            if isinstance(item, Folder):
                folder_depth = self._get_max_depth_recursive(item.items, current_depth + 1)
                max_depth = max(max_depth, folder_depth)
        return max_depth

    def count_by_method(self) -> Dict[str, int]:
        """
        Count requests by HTTP method.
        
        Returns:
            Dictionary mapping HTTP methods to their counts
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> by_method = stats.count_by_method()
            >>> print(f"GET requests: {by_method.get('GET', 0)}")
            >>> print(f"POST requests: {by_method.get('POST', 0)}")
        """
        methods = [request.method.upper() for request in self.collection.get_requests()]
        return dict(Counter(methods))

    def count_by_auth(self) -> Dict[str, int]:
        """
        Count requests by authentication type.
        
        This method resolves the effective authentication for each request
        by considering the authentication hierarchy (request > folder > collection).
        
        Returns:
            Dictionary mapping auth types to their counts.
            Uses "none" for requests with no authentication.
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> by_auth = stats.count_by_auth()
            >>> print(f"Bearer auth: {by_auth.get('bearer', 0)}")
            >>> print(f"No auth: {by_auth.get('none', 0)}")
        """
        auth_types = []
        for request in self.collection.get_requests():
            # Try to get effective auth using the introspection module
            try:
                resolved_auth = request.get_effective_auth(collection=self.collection)
                if resolved_auth.auth:
                    auth_types.append(resolved_auth.auth.type)
                else:
                    auth_types.append("none")
            except Exception:
                # Fallback to simple request-level auth check
                if request.auth:
                    auth_types.append(request.auth.type)
                else:
                    auth_types.append("none")
        
        return dict(Counter(auth_types))

    def get_avg_requests_per_folder(self) -> float:
        """
        Calculate average requests per folder.
        
        Returns:
            Average number of requests per folder.
            Returns 0.0 if there are no folders.
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> avg = stats.get_avg_requests_per_folder()
            >>> print(f"Average requests per folder: {avg:.2f}")
        """
        total_folders = self.count_folders()
        if total_folders == 0:
            return 0.0
        
        total_requests = self.count_requests()
        return total_requests / total_folders

    def to_json(self, indent: int = 2) -> str:
        """
        Export statistics to JSON format.
        
        Args:
            indent: Number of spaces for JSON indentation (default: 2)
        
        Returns:
            JSON string representation of statistics
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> json_output = stats.to_json()
            >>> with open("stats.json", "w") as f:
            ...     f.write(json_output)
        """
        data = self.collect()
        return json.dumps(data, indent=indent)

    def to_csv(self) -> str:
        """
        Export statistics to CSV format.
        
        The CSV format includes:
        - Summary statistics (total_requests, total_folders, etc.)
        - Breakdown by HTTP method
        - Breakdown by authentication type
        
        Returns:
            CSV string representation of statistics
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> csv_output = stats.to_csv()
            >>> with open("stats.csv", "w") as f:
            ...     f.write(csv_output)
        """
        data = self.collect()
        output = StringIO()
        writer = csv.writer(output)
        
        # Write summary statistics
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Requests", data["total_requests"]])
        writer.writerow(["Total Folders", data["total_folders"]])
        writer.writerow(["Max Nesting Depth", data["max_nesting_depth"]])
        writer.writerow(["Avg Requests Per Folder", f"{data['avg_requests_per_folder']:.2f}"])
        writer.writerow([])  # Empty row
        
        # Write requests by method
        writer.writerow(["HTTP Method", "Count"])
        for method, count in sorted(data["requests_by_method"].items()):
            writer.writerow([method, count])
        writer.writerow([])  # Empty row
        
        # Write requests by auth type
        writer.writerow(["Auth Type", "Count"])
        for auth_type, count in sorted(data["requests_by_auth"].items()):
            writer.writerow([auth_type, count])
        
        return output.getvalue()

    def clear_cache(self) -> None:
        """
        Clear the statistics cache.
        
        Call this method if the collection has been modified and you want
        to recalculate statistics.
        
        Examples:
            >>> stats = collection.get_statistics()
            >>> data1 = stats.collect()  # Calculates and caches
            >>> # ... modify collection ...
            >>> stats.clear_cache()
            >>> data2 = stats.collect()  # Recalculates
        """
        self._cache = None

    def __repr__(self) -> str:
        return f"CollectionStatistics(collection='{self.collection.info.name}')"
