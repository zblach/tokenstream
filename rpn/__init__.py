# context-free grammar for reverse polish notation

# expression -> expression expression operand | number
# operand -> + | - | * | /
# number -> FLOAT_PATTERN


from calculator.tokenizer import UnexpectedEndOfExpressionError
from .tokenizer import Operator, Tokenizer
from tokenizer import Number, TokenError, UnexpectedTokenError
from collections import deque
from typing import Deque


def evaluate(expression: str) -> float:
    """
    Evaluate an arithmetic expression given as a string and return the result as a float.

    Args:
        expression (str): The arithmetic expression to evaluate.

    Returns:
        float: The result of the evaluated expression.

    Raises:
        UnexpectedTokenError: If there are one or more unexpected tokens at the end of the expression.
    """

    values: Deque[float] = deque()
    try:
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
                case _:
                    raise UnexpectedTokenError(token)
    except TokenError as e:
        print(
            rf"""Invalid expression!
> {expression}
  {' ' * e.token.start}{'^' * (e.token.end - e.token.start)}"""
        )
        raise e

    if len(values) != 1:
        raise UnexpectedEndOfExpressionError()

    return values.pop()
