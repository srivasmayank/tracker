import csv
import io
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ExportFormatter(ABC):
    """
    Abstract Strategy interface for serializing expense dataset into downloadable byte streams.
    Adheres to Open/Closed Principle (OCP): new formats (e.g. Parquet, Excel, PDF) can be
    added without modifying existing business logic or API endpoints.
    """

    @abstractmethod
    def format(self, records: List[Dict[str, Any]]) -> bytes:
        """Serialize records into raw bytes."""
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """MIME type for HTTP streaming response."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension including leading dot (e.g., '.csv')."""
        pass


class CSVExportFormatter(ExportFormatter):
    """
    Serializes records to standard RFC 4180 comma-separated values (UTF-8 with BOM for Excel compatibility).
    """

    @property
    def content_type(self) -> str:
        return "text/csv; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".csv"

    def format(self, records: List[Dict[str, Any]]) -> bytes:
        output = io.StringIO()
        if not records:
            headers = ["id", "date", "category", "amount", "description", "payment_method", "created_at"]
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
        else:
            headers = list(records[0].keys())
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for row in records:
                # Ensure all values are safely stringified
                writer.writerow({k: (str(v) if v is not None else "") for k, v in row.items()})

        # Prepend UTF-8 BOM so Microsoft Excel opens it without encoding glitches
        bom = "\ufeff"
        return (bom + output.getvalue()).encode("utf-8")


class JSONExportFormatter(ExportFormatter):
    """
    Serializes records to formatted JSON array.
    """

    @property
    def content_type(self) -> str:
        return "application/json"

    @property
    def file_extension(self) -> str:
        return ".json"

    def format(self, records: List[Dict[str, Any]]) -> bytes:
        serialized = json.dumps(records, indent=2, default=str)
        return serialized.encode("utf-8")


class ExportFormatterFactory:
    """
    Factory Pattern for instantiating the appropriate strategy.
    """
    _formatters = {
        "CSV": CSVExportFormatter,
        "JSON": JSONExportFormatter,
    }

    @classmethod
    def get_formatter(cls, format_type: str) -> ExportFormatter:
        normalized = format_type.upper().strip()
        formatter_cls = cls._formatters.get(normalized)
        if not formatter_cls:
            raise ValueError(f"Unsupported export format '{format_type}'. Supported: {list(cls._formatters.keys())}")
        return formatter_cls()
