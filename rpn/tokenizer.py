import re
from typing import Iterator, Literal, get_args
from tokenizer import (
    FLOAT_PATTERN,
    InvalidTokenError,
    Number,
    Token,
    TokenStream,
    Invalid,
)

Operators = Literal["+", "-", "*", "/"]


class Operator(Token[Operators]): ...


TokenType = Number | Operator | Invalid


class Tokenizer(TokenStream[TokenType]):
    # this grammar is a bit simpler, as it does require spaces. It cannot afford ambiguity with leading operators.
    #   e.g. "1 + 2 -3 4" cannot be easily disambiguated from "1 + 2 - 3 4" without fully parsing the expression.
    GRAMMAR = re.compile(
        rf"""
        (?:
            (?P<number>{FLOAT_PATTERN.pattern})
            |
            (?P<operator>[+\-*/])
            |
            (?P<invalid>\S+)
        )
    """,
        re.VERBOSE,
    )

    def _tokenize(self, expression: str) -> Iterator[TokenType]:
        for match in Tokenizer.GRAMMAR.finditer(expression):
            start, end = match.span()
            val = match.group()
            match match.lastgroup:
                case "number":
                    yield Number(float(val), start, end)
                case "operator" if val in get_args(Operators):
                    yield Operator(val, start, end)  # type: ignore
                case "invalid" | _:
                    raise InvalidTokenError(Invalid(val, start, end))
