class DomainError(Exception):
    def __init__(self, code: str, message: str, details: list | None = None):
        self.code, self.message, self.details = code, message, details or []
        super().__init__(message)

STATUS = {"unauthorized":401,"forbidden":403,"not_found":404,"conflict":409,
          "too_large":413,"invalid":422,"recommendations_not_implemented":501,"unavailable":503}
