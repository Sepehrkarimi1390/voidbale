class VoidBaleError(Exception):
    pass

class BaleAPIError(VoidBaleError):
    def __init__(self, description, method=None, status=None, parameters=None):
        self.description = str(description)
        self.method = method
        self.status = status
        self.parameters = parameters or {}
        super().__init__(self.description)

class RequestError(VoidBaleError):
    pass
