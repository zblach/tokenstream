import re
from typing import Iterator, Literal, LiteralString, Optional, TypeVar, Union, get_args

import tokenizer

from tokenizer import FLOAT_PATTERN, Number, Invalid, Token


# Define the regular expression pattern for tokenization

# String literal types for operators and parentheses, used for type hinting
Operators = Literal["+", "-", "*", "/", "**", "^"]
Parentheses = Literal["(", ")"]

# The actual token value type, which can be a number, operator, or parenthesis. str is used for invalid tokens.
TokenValue = TypeVar("TokenValue", bound=Union[Operators, Parentheses, float, str])


class Operator(Token[Operators]): ...


class Parenthesis(Token[Parentheses]): ...


# Union of all token types (TODO: get subclasses of Token dynamically?)
TokenType = Number | Operator | Parenthesis | Invalid


# Exceptions for tokenization and parsing errors


class UnexpectedEndOfExpressionError(ValueError):
    def __init__(self):
        super().__init__("Unexpected end of expression")


# Token stream


class Tokenizer(tokenizer.TokenStream[TokenType]):
    """
    A stream of tokens representing an arithmetic expression.
    """

    GRAMMAR = re.compile(
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

    OPERATORS: tuple[LiteralString, ...] = get_args(Operators)
    PARENTHESES: tuple[LiteralString, ...] = get_args(Parentheses)

    _lookahead: Optional[TokenType] = None

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
        for match in Tokenizer.GRAMMAR.finditer(expression):
            tok, typ = match.group(), match.lastgroup
            start, end = match.span()
            match typ:
                # Handle signs without a space between the sign and the number
                #   eg. "4-3" => [4, "-", 3], not [4, -3]
                #   eg. "+3+3" => [3, "+", 3], not [3, 3] (or ["+", 3, "+", 3] or ["+", 3, 3])
                # We still want signed numbers to have a higher match precedence, so we can safely assume that an extra sign is an operator.
                # The fact that the grammar doesn't allow for two numbers in sequence is a parser concern, not a tokenizer concern.
                case "number" if previousType == "number" and tok[0] in ("-", "+"):
                    yield Operator(tok[0], start, start + 1)
                    yield Number(float(tok[1:]), start + 1, end)

                case "number":
                    yield Number(float(tok), start, end)

                case "operator" if tok in Tokenizer.OPERATORS:
                    yield Operator(tok, start, end)  # type: ignore

                case "parenthesis" if tok in Tokenizer.PARENTHESES:
                    yield Parenthesis(tok, start, end)  # type: ignore

                case "invalid" | _:
                    yield Invalid(tok, start, end)

            previousType = typ

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
            raise tokenizer.TokenError(
                "Cannot reinsert more than one token", self._lookahead
            )
        self._lookahead = token
