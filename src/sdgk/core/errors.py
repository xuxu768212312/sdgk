class SdgkError(Exception):
    """Base project error."""


class HardGateError(SdgkError):
    """Raised when a formal delivery hard gate fails."""


class ReviewRequiredError(SdgkError):
    """Raised when deterministic logic cannot safely decide."""

