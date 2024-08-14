from calculator.tokenizer import UnexpectedEndOfExpressionError
from .tokenizer import Operator, Tokenizer
from tokenizer import (
    Invalid,
    InvalidTokenError,
    Number,
    UnexpectedTokenError,
)
from collections import deque
from typing import Deque

# context-free grammar for reverse polish notation

# expression -> expression expression operand | number
#    operand -> "+" | "-" | "*" | "/"
#     number -> FLOAT_PATTERN


def evaluate(expression: str) -> float:
    """
    Evaluate an arithmetic expression given as a string and return the result as a float.

    Args:
        expression (str): The arithmetic expression to evaluate.

    Returns:
        float: The result of the evaluated expression.

    Raises:
        InvalidTokenError: If an invalid token is encountered.
        UnexpectedTokenError: If we encounter a token where it's not expected (i.e. insufficient values for operation).
        UnexpectedEndOfExpressionError: If the expression ends unexpectedly (i.e. unprocessed values).
    """

    values: Deque[float] = deque()
    for token in Tokenizer(expression):
        match token:
            case Number(value):
                values.append(value)
            case Operator(operator) if len(values) >= 2:
                right, left = values.pop(), values.pop()
                match operator:
                    case "+":
                        values.append(left + right)
                    case "-":
                        values.append(left - right)
                    case "*":
                        values.append(left * right)
                    case "/":
                        values.append(left / right)
            case Invalid():
                raise InvalidTokenError(token)
            case _:
                raise UnexpectedTokenError(token)

    if len(values) != 1:
        raise UnexpectedEndOfExpressionError()

    return values.pop()
