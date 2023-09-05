from termcolor import colored

class InsufficientCapitalException(Exception):
    def __init__(self, message="⚠️ERROR: El capital es insuficiente para realizar esta estrategia en su totalidad"):
        message = colored(message, 'blue')
        super().__init__(message)