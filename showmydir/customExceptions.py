class CreateModeNotUpdatedError(Exception):
    """Raised when a new CreateMode is added but not handled in logic."""

    def __init__(self, message: str | None = None):
        super().__init__(message or "Program is not updated here.")


class GitIgnoreFileNotFoundError(Exception):
    """Raised when a .gitignore file is requested but not found."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "No such gitignore file found")


class InvalidNodeNameError(Exception):
    def __init__(self, name: str, message: str | None = None) -> None:
        super().__init__(message or f"Invalid node name: {name}")
