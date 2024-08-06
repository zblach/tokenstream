import re
from abc import ABC
from dataclasses import dataclass
from typing import Generic, Iterator, Literal, Optional, TypeVar, Union, get_args

FLOAT_PATTERN = re.compile(r"[-+]?\d*\.?\d+([eE][-+]?\d+)?")

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

# String literal types for operators and parentheses, used for type hinting
Operators = Literal["+", "-", "*", "/", "**", "^"]
Parentheses = Literal["(", ")"]

# The actual token value type, which can be a number, operator, or parenthesis. str is used for invalid tokens.
TokenValue = TypeVar("TokenValue", bound=Union[Operators, Parentheses, float, str])


# Define the token classes
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


class Number(Token[float]): ...


class Operator(Token[Operators]): ...


class Parenthesis(Token[Parentheses]): ...


class Invalid(Token[str]): ...


# Union of all token types (TODO: get subclasses of Token dynamically?)
TokenType = Number | Operator | Parenthesis | Invalid


# Exceptions for tokenization and parsing errors


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


class UnexpectedEndOfExpressionError(ValueError):
    def __init__(self):
        super().__init__("Unexpected end of expression")


# Token stream


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
                # Handle signs without a space between the sign and the number
                #   eg. "4-3" => [4, "-", 3], not [4, -3]
                #   eg. "+3+3" => [3, "+", 3], not [3, 3] (or ["+", 3, "+", 3] or ["+", 3, 3])
                # We still want signed numbers to have a higher match precedence, and it's not legal to have two numbers in a row, so we can safely assume that an extra sign is an operator.
                case "number" if previousType == "number" and tok[0] in ("-", "+"):
                    yield Operator(tok[0], start, start + 1)
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

    def reinsert(self, token: TokenType):
        """
        Reinsert a token into the stream for future use.

        Args:
            Token: The token to push back to the front.
        """
        if self._lookahead is not None:
            raise TokenError("Cannot reinsert more than one token", self._lookahead)
        self._lookahead = token
