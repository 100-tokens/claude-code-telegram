"""Custom exceptions for CLI operations."""


class CLIError(Exception):
    """Base exception for CLI errors."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class ConfigError(CLIError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=1)


class DirectoryError(CLIError):
    """Exception raised for directory access errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=1)


class RuntimeError(CLIError):
    """Exception raised for runtime errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=2)
