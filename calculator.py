from typing import Optional
from tokenizer import (
    Number,
    Operator,
    Parenthesis,
    TokenError,
    TokenStream,
    UnexpectedEndOfExpressionError,
    UnexpectedTokenError,
)

# context-free grammar for the parsing logic

# expression -> term {("+" | "-") term}
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
    tokens = TokenStream(expression)
    try:
        result = _expression(tokens)
        if (token := next(tokens, None)) != None:
            raise UnexpectedTokenError(token)
    except TokenError as e:
        print(
            rf"""Invalid expression!
> {expression}
  {' ' * e.token.start}{'^' * (e.token.end - e.token.start)}"""
        )
        raise e

    return result


def _expression(tokens: TokenStream, intermediate: Optional[float] = None) -> float:
    """
    Parse and evaluate an expression, handling addition and subtraction.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.
        intermediate (Optional[float]): An intermediate value used in recursive parsing (default is None).

    Returns:
        float: The result of the parsed expression.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    if intermediate is None:
        intermediate = _term(tokens)

    match token := next(tokens, None):
        case Operator("+"):
            return _expression(tokens, intermediate + _term(tokens))
        case Operator("-"):
            return _expression(tokens, intermediate - _term(tokens))
        case None:
            return intermediate
        case _:
            tokens.reinsert(token)
            return intermediate


def _term(tokens: TokenStream, intermediate: Optional[float] = None) -> float:
    """
    Parse and evaluate a term, handling multiplication and division.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.
        intermediate (Optional[float]): An intermediate value used in recursive parsing (default is None).

    Returns:
        float: The result of the parsed term.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    if intermediate is None:
        intermediate = _factor(tokens)

    match token := next(tokens, None):
        case Operator("*"):
            return _term(tokens, intermediate * _factor(tokens))
        case Operator("/"):
            return _term(tokens, intermediate / _factor(tokens))
        case None:
            return intermediate
        case _:
            tokens.reinsert(token)
            return intermediate


def _factor(tokens: TokenStream, intermediate: Optional[float] = None) -> float:
    """
    Parse and evaluate a factor, handling exponentiation.

    Args:
        tokens (TokenStream): An iterator of tokens representing the expression.
        intermediate (Optional[float]): An intermediate value used in recursive parsing (default is None).

    Returns:
        float: The result of the parsed factor.

    Raises:
        UnexpectedEndOfExpressionError: If there are unexpected tokens at the end of the expression.
        UnexpectedTokenError: If there is an invalid token in the expression.
    """
    if intermediate is None:
        intermediate = _base(tokens)

    match token := next(tokens, None):
        case Operator("**") | Operator("^"):
            return intermediate ** _factor(tokens)
        case None:
            return intermediate
        case _:
            tokens.reinsert(token)
            return intermediate


def _base(tokens: TokenStream) -> float:
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


if __name__ == "__main__":
    import unittest
    from test_calculator import TestEvaluate
    from test_tokenizer import TestTokenStream

    loader = unittest.TestLoader()
    loader.loadTestsFromTestCase(TestEvaluate)
    loader.loadTestsFromTestCase(TestTokenStream)

    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2), testLoader=loader)
