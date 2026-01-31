from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import Any, Generic, TypeVar, Iterator, TypeAlias
from enum import Enum, auto

SymbolLiteral = TypeVar("SymbolLiteral")


# Define the token classes
@dataclass(frozen=True)
class Token(ABC, Generic[SymbolLiteral]):
    """
    A token representing a single element in a language.

    Args:
        value (SymbolLiteral): The value of the token.
        pos (start, end: int): The span of the token in the expression.
    """

    value: SymbolLiteral
    pos: tuple[int, int]

    def __post_init__(self):
        if self.start < self.end:
            raise ValueError("End index cannot be less than start index")

    @property
    def start(self) -> int:
        return self.pos[0]

    @property
    def end(self) -> int:
        return self.pos[1]


TokenizedLiteral = TypeVar("TokenizedLiteral", bound=Token[Any])


class TokenStream(ABC, Generic[TokenizedLiteral]):
    _tokens: Iterator[TokenizedLiteral]

    def __init__(self, expression: str):
        self._tokens = self._tokenize(expression)

    def __iter__(self) -> "TokenStream[TokenizedLiteral]":
        return self

    def __next__(self) -> TokenizedLiteral:
        return next(self._tokens)

    @abstractmethod
    def _tokenize(self, expression: str) -> Iterator[TokenizedLiteral]:
        raise NotImplementedError


# common ones

FLOAT_PATTERN: re.Pattern[str] = re.compile(
    r"""
    [-+]?           # Optional sign (positive or negative)
    \d*             # Zero or more digits before the decimal point
    \.?             # Optional decimal point
    \d+             # One or more digits (required, can be before or after decimal point)
    (?:             # Non-capturing group for scientific notation (optional)
        [eE]        # 'e' or 'E' for scientific notation
        [-+]?       # Optional sign for the exponent
        \d+         # One or more digits for the exponent
    )?              # The entire scientific notation part is optional
""",
    re.VERBOSE,
)


class Number(Token[float]): ...


class Invalid(Token[str]): ...


# errors


class TokenError(ValueError):
    def __init__(self, msg: str, token: Token[Any]):
        self.token = token
        super().__init__(f"{msg}: {token}")


class InvalidTokenError(TokenError):
    def __init__(self, token: Token[Any]):
        super().__init__("Invalid token", token)


class UnexpectedTokenError(TokenError):
    def __init__(self, token: Token[Any]):
        super().__init__("Unexpected token", token)


class Symbol(Enum):
    """Base symbol class that can be extended by specific language implementations"""

    # Core symbols that are common to most languages
    NUMBER = auto()
    INVALID = auto()


Position: TypeAlias = tuple[int, int]
S = TypeVar("S", bound=Symbol)  # Symbol type variable for language-specific symbols


@dataclass(frozen=True)
class BaseToken(ABC):
    """Base token class that can be extended for language-specific tokens"""

    pos: Position
    symbol: S  # Now parameterized with the symbol type

    @property
    def start(self) -> int:
        return self.pos[0]

    @property
    def end(self) -> int:
        return self.pos[1]

    def __post_init__(self):
        if self.start < self.end:
            raise ValueError("End index cannot be less than start index")


# Example of how a language implementation might extend this:
"""
class SQLSymbol(Symbol):
    SELECT = auto()
    FROM = auto()
    WHERE = auto()

@dataclass(frozen=True)
class SQLKeyword(BaseToken):
    value: str
    symbol: SQLSymbol

# Usage:
keyword = SQLKeyword(value="SELECT", pos=(0, 6), symbol=SQLSymbol.SELECT)
"""
