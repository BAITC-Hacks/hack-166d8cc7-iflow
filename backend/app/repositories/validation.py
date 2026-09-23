class SourceValidationError(ValueError):
    """Sanitized source locations; never retain uploaded values."""
    def __init__(self, details: list[dict]):
        super().__init__("Source data validation failed")
        self.details = details
