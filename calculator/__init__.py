from tokenizer import Invalid, InvalidTokenError, TokenError, UnexpectedTokenError
from .tokenizer import (
    Number,
    Operator,
    Parenthesis,
    Tokenizer,
    UnexpectedEndOfExpressionError,
)

# context-free grammar for the parsing logic

# expression -> term {("+" | "-") expression}
#       term -> factor {("*" | "/") factor}
#     factor -> base {("**" | "^") base}
#       base -> number | {"-"} "(" expression ")"
#     number -> FLOAT_PATTERN


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
    tokens = Tokenizer(expression)
    try:
        result = _expression(tokens)
        match (token := next(tokens, None)):
            case None:
                pass
            case Invalid():
                raise InvalidTokenError(token)
            case _:
                raise UnexpectedTokenError(token)
    except TokenError as e:
        print(
            rf"""Invalid expression!
> {expression}
  {' ' * e.token.start}{'^' * (e.token.end - e.token.start)}"""
        )
        raise e

    return result


def _expression(tokens: Tokenizer) -> float:
    """
    Parse and evaluate an expression, handling addition and subtraction.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.

    Returns:
        float: The result of the parsed expression.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    term = _term(tokens)

    match token := next(tokens, None):
        case Operator("+"):
            return term + _expression(tokens)
        case Operator("-"):
            return term - _expression(tokens)
        case None:
            return term
        case _:
            tokens.reinsert(token)
            return term


def _term(tokens: Tokenizer) -> float:
    """
    Parse and evaluate a term, handling multiplication and division.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.

    Returns:
        float: The result of the parsed term.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    factor = _factor(tokens)

    match token := next(tokens, None):
        case Operator("*"):
            return factor * _factor(tokens)
        case Operator("/"):
            return factor / _factor(tokens)
        case None:
            return factor
        case _:
            tokens.reinsert(token)
            return factor


def _factor(tokens: Tokenizer) -> float:
    """
    Parse and evaluate a factor, handling exponentiation.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.

    Returns:
        float: The result of the parsed factor.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    base = _base(tokens)

    match token := next(tokens, None):
        case Operator("**") | Operator("^"):
            return base ** _factor(tokens)
        case None:
            return base
        case _:
            tokens.reinsert(token)
            return base


def _base(tokens: Tokenizer) -> float:
    """
    Parse and evaluate a base value, which can be a number or a parenthesized expression.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.

    Returns:
        float: The parsed base value.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    match token := next(tokens, None):
        case Number(value=value):
            return value
        case Operator("-"):
            return -_expression(tokens)
        case Parenthesis("("):
            value = _expression(tokens)
            match token := next(tokens, None):
                case Parenthesis(")"):
                    return value
                case None:
                    raise UnexpectedEndOfExpressionError()
                case _:
                    raise UnexpectedTokenError(token)
        case None:
            raise UnexpectedEndOfExpressionError()
        case _:
            raise UnexpectedTokenError(token)
