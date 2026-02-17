class BaseEngineException(Exception):
    """Root exception for all engine-related errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class KernelError(BaseEngineException):
    """Raised when a core kernel operation fails."""

class ModuleError(BaseEngineException):
    """Raised when a module operation fails."""

class ModuleLoadError(ModuleError):
    """Raised when a module fails to load or initialize."""

class AccessDeniedError(BaseEngineException):
    """Raised when a security or permission violation occurs."""

class DomainException(BaseEngineException):
    """Base for business-logic related exceptions."""

class ResourceNotFoundError(DomainException):
    """Raised when a requested resource (record, file) is not found."""
