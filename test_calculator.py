from dataclasses import dataclass
import re
import unittest
from abc import ABC
from typing import Optional, Iterator, Union, Generic, TypeVar, Literal, get_args

# Define the regular expression pattern for matching floating-point numbers, including negative numbers
FLOAT_PATTERN = re.compile(
    r"""
    -?              # Optional leading negative sign
    \d+             # Integral part
    (\.\d+)?        # Optional fractional part
""",
    re.VERBOSE,
)

# Define the regular expression pattern for tokenization
TOKEN_PATTERN = re.compile(
    rf"""
        (?:
            (?P<number>{FLOAT_PATTERN.pattern})   # Named group for numbers (integer or floating-point)
            |
            (?P<operator>\*\*|[+\-*/\^])          # Named group for operators
            |
            (?P<parenthesis>[()])                 # Named group for parentheses
            |
            (?P<invalid>\S+)                      # Named group for any other non-whitespace characters
        )
    """,
    re.VERBOSE,
)

Operators = Literal["+", "-", "*", "/", "**", "^"]
Parentheses = Literal["(", ")"]
TokenValue = TypeVar("TokenValue", bound=Union[Operators, Parentheses, float, str])


@dataclass(frozen=True)
class Token(ABC, Generic[TokenValue]):
    """
    A token representing a single element in an arithmetic expression.

    Args:
        value (TokenValue): The value of the token.
        start (int): The starting index of the token in the expression.
        end (int): The ending index of the token in the expression.
    """

    value: TokenValue
    start: int
    end: int

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End index cannot be less than start index")


class Number(Token[float]):
    def __init__(self, value: float, start: int, end: int):
        super().__init__(value, start, end)


class Operator(Token[Operators]):
    def __init__(self, value: Operators, start: int, end: int):
        super().__init__(value, start, end)


class Parenthesis(Token[Parentheses]):
    def __init__(self, value: Parentheses, start: int, end: int):
        super().__init__(value, start, end)


class Invalid(Token[str]):
    def __init__(self, value: str, start: int, end: int):
        super().__init__(value, start, end)


TokenType = Token[Operators] | Token[Parentheses] | Token[str] | Token[float]

# Define custom exceptions


class UnexpectedEndOfExpressionError(ValueError):
    def __init__(self):
        super().__init__("Unexpected end of expression")


class TokenError(ValueError):
    def __init__(self, msg: str, token: TokenType):
        self.token = token
        super().__init__(f"{msg}: {token}")


class InvalidTokenError(TokenError):
    def __init__(self, token: TokenType):
        super().__init__("Invalid token", token)


class UnexpectedTokenError(ValueError):
    def __init__(self, token: TokenType):
        super().__init__("Unexpected token", token)


class TokenStream:
    """
    A stream of tokens representing an arithmetic expression.
    """

    def __init__(self, expression: str):
        self._tokens: Iterator[TokenType] = self._tokenize(expression)
        self._lookahead: Optional[TokenType] = None

    def _tokenize(self, expression: str) -> Iterator[TokenType]:
        """
        Tokenize the input expression string into individual tokens.

        Args:
            expression (str): The input string to tokenize.

        Yields:
            Token: Each token extracted from the expression.

        Raises:
            InvalidTokenError: If an invalid token is encountered.
        """
        previousType = ""
        for match in TOKEN_PATTERN.finditer(expression):
            tok, typ = match.group(), match.lastgroup
            start, end = match.span()
            match typ:
                # Handle subtraction without a space between the sign and the number, eg. "4-3" => [4, "-", 3], not [4, -3]
                # We still want negative numbers to have a higher match precedence, and it's not legal to have two numbers in a row, so we can safely assume that the "-" is an operator.
                case "number" if previousType == "number" and tok[0] == "-":
                    yield Operator("-", start, start + 1)
                    yield Number(float(tok[1:]), start + 1, end)

                case "number":
                    yield Number(float(tok), start, end)

                case "operator" if tok in get_args(Operators):
                    yield Operator(tok, start, end)  # type: ignore

                case "parenthesis" if tok in get_args(Parentheses):
                    yield Parenthesis(tok, start, end)  # type: ignore

                case "invalid" | _:
                    raise InvalidTokenError(Invalid(tok, start, end))

            previousType = typ

    def __iter__(self) -> "TokenStream":
        return self

    def __next__(self) -> TokenType:
        if self._lookahead is not None:
            token, self._lookahead = self._lookahead, None
            return token
        return next(self._tokens)

    def push_back(self, token: TokenType):
        """
        Push back a token into the stream for future use.

        Args:
            Token: The token to push back.
        """
        if self._lookahead is not None:
            raise TokenError("Cannot push back more than one token", self._lookahead)
        self._lookahead = token


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
    result = _expression(tokens)
    if (token := next(tokens, None)) != None:
        raise UnexpectedTokenError(token)
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
            tokens.push_back(token)
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
            tokens.push_back(token)
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
            tokens.push_back(token)
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


# Test class
class TestEvaluate(unittest.TestCase):
    def test_simple_expressions(self):
        self.assertEqual(evaluate("3 + 4 * 5 - 6 / 2"), 3 + 4 * 5 - 6 / 2)
        self.assertEqual(evaluate("2 + 3"), 2 + 3)
        self.assertEqual(evaluate("10 - 2 * 5"), 10 - 2 * 5)
        self.assertEqual(evaluate("7"), 7)

    def test_parentheses(self):
        self.assertEqual(evaluate("(3 + 4) * 5"), (3 + 4) * 5)
        self.assertEqual(evaluate("2 * (3 + 4)"), 2 * (3 + 4))
        self.assertEqual(evaluate("(2 + 3) * (5 - 1)"), (2 + 3) * (5 - 1))
        self.assertEqual(evaluate("(7)"), 7)
        self.assertEqual(evaluate("(-7)"), -7)
        self.assertEqual(evaluate("-(7)"), -7)

    def test_unary_negative(self):
        self.assertEqual(evaluate("-3"), -3)
        self.assertEqual(evaluate("-3 + 4"), -3 + 4)
        self.assertEqual(evaluate("3 + -4"), 3 + -4)
        self.assertEqual(evaluate("-3 * -4"), -3 * -4)
        self.assertEqual(evaluate("3 * -4"), 3 * -4)
        self.assertEqual(evaluate("-(-3)"), -(-3))
        self.assertEqual(evaluate("--3"), 3)

    def test_order_of_operations(self):
        self.assertEqual(evaluate("3 + 4 * 5"), 3 + 4 * 5)
        self.assertEqual(evaluate("3 + 4 * 5 - 6 / 2"), 3 + 4 * 5 - 6 / 2)
        self.assertEqual(evaluate("2 ** 3 + 4"), 2**3 + 4)
        self.assertEqual(evaluate("2 + 3 ** 2"), 2 + 3**2)
        self.assertEqual(evaluate("2 * 3 ** 2"), 2 * 3**2)
        self.assertEqual(evaluate("2 ** 3 * 2"), 2**3 * 2)
        self.assertEqual(evaluate("2 ** 3 ** 2"), 2**3**2)
        self.assertEqual(evaluate("2 ** (3 + 2)"), 2 ** (3 + 2))
        self.assertEqual(evaluate("(3 + 2) ** 2"), (3 + 2) ** 2)

    def test_exponentiation(self):
        self.assertEqual(evaluate("2 ** 3"), 2**3)
        self.assertEqual(evaluate("2 ** 3 ** 2"), 2**3**2)
        self.assertEqual(evaluate("2 ** (3 ** 2)"), 2 ** (3**2))
        self.assertEqual(evaluate("(2 ** 3) ** 2"), (2**3) ** 2)

    def test_invalid_token(self):
        with self.assertRaises(InvalidTokenError):
            evaluate("3 + 4 & 5")
        with self.assertRaises(UnexpectedTokenError):
            evaluate("+ 4")

    def test_spaceless_negative(self):
        self.assertEqual(evaluate("3-4"), 3 - 4)
        self.assertEqual(evaluate("3--4"), 3 - -4)
        self.assertEqual(evaluate("3- -4"), 3 - -4)
        self.assertEqual(evaluate("-3-4"), -3 - 4)
        self.assertEqual(evaluate("-3--4"), -3 - -4)
        self.assertEqual(evaluate("-3- -4"), -3 - -4)

    def test_float_math(self):
        self.assertAlmostEqual(evaluate("1.5 + 2.5"), 1.5 + 2.5)
        self.assertAlmostEqual(evaluate("1.5 * 2.5"), 1.5 * 2.5)
        self.assertAlmostEqual(evaluate("1.5 / 2.5"), 1.5 / 2.5)
        self.assertAlmostEqual(evaluate("1.5 ** 2.5"), 1.5**2.5)

    def test_invalid_expression(self):
        with self.assertRaises(UnexpectedEndOfExpressionError):
            evaluate("3 +")
        with self.assertRaises(InvalidTokenError):
            evaluate("3 + 4 & 5")
        with self.assertRaises(UnexpectedTokenError):
            evaluate("+ 4")
        with self.assertRaises(UnexpectedTokenError):
            evaluate("3 + 4 )")

    def test_mismatched_parentheses(self):
        """Test for mismatched parentheses"""
        with self.assertRaises(UnexpectedEndOfExpressionError):
            evaluate("(3 + 4")  # Missing closing parenthesis
        with self.assertRaises(UnexpectedTokenError):
            evaluate(")3 + 4(")  # Unexpected close parenthesis
        with self.assertRaises(UnexpectedEndOfExpressionError):
            evaluate("3 + (4 * (5 - 2")  # Missing closing parenthesis


def tokens(expression: str) -> list[Union[str, float]]:
    return [v.value for v in TokenStream(expression)]


class TestTokenStream(unittest.TestCase):
    def test_unary_negative(self):
        expression = "-3"
        expected_tokens = [-3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_double_negative(self):
        expression = "--3"
        expected_tokens = ["-", -3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_no_spaces(self):
        expression = "4-3"
        expected_tokens = [4, "-", 3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_double_nested_negative(self):
        expression = "-(-3)"
        expected_tokens = ["-", "(", -3, ")"]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_valid_expression(self):
        expression = "3 + 4 * 10 - 5 / 2 ** 2"
        expected_tokens = [3, "+", 4, "*", 10, "-", 5, "/", 2, "**", 2]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_invalid_token(self):
        expression = "3 + 4 & 10"
        with self.assertRaises(InvalidTokenError) as context:
            list(TokenStream(expression))
        self.assertEqual(str(context.exception.token.value), "&")

    def test_empty_expression(self):
        expression = ""
        self.assertEqual(tokens(expression), [])

    def test_expression_with_whitespace(self):
        expression = "  3   + 4   * 10 -5 / 2 **  2   "
        expected_tokens = [3, "+", 4, "*", 10, "-", 5, "/", 2, "**", 2]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_expression_with_parentheses(self):
        expression = "(3 + 4) * (10 - 5) / (2 ** 2)"
        expected_tokens = [
            "(",
            3,
            "+",
            4,
            ")",
            "*",
            "(",
            10,
            "-",
            5,
            ")",
            "/",
            "(",
            2,
            "**",
            2,
            ")",
        ]
        self.assertEqual(tokens(expression), expected_tokens)


if __name__ == "__main__":
    unittest.main()
