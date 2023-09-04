class InsufficientCapitalException(Exception):
    def __init__(self, message="El capital es insuficiente para realizar esta estrategia en su totalidad"):
        super().__init__(message)