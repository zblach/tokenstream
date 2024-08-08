from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import Any, Generic, TypeVar, Iterator

SymbolLiteral = TypeVar("SymbolLiteral")


# Define the token classes
@dataclass(frozen=True)
class Token(ABC, Generic[SymbolLiteral]):
    """
    A token representing a single element in an arithmetic expression.

    Args:
        value (SymbolLiteral): The value of the token.
        start (int): The starting index of the token in the expression.
        end (int): The ending index of the token in the expression.
    """

    value: SymbolLiteral
    start: int
    end: int

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End index cannot be less than start index")


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

FLOAT_PATTERN = re.compile(r"[-+]?\d*\.?\d+([eE][-+]?\d+)?")


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
