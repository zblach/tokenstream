import re
from typing import Final, Iterator, Literal, Tuple, final, get_args, cast
from tokenizer import (
    FLOAT_PATTERN,
    Number,
    Token,
    TokenStream,
    Invalid,
)

Operators = Literal["+", "-", "*", "/"]


class Operator(Token[Operators]): ...


TokenType = Number | Operator | Invalid


@final
class Tokenizer(TokenStream[TokenType]):
    # this grammar is a bit simpler, as it does require spaces. It cannot afford ambiguity with leading operators.
    #   e.g. "1 + 2 -3 4" cannot be easily disambiguated from "1 + 2 - 3 4" without fully parsing the expression.
    GRAMMAR: Final[re.Pattern[str]] = re.compile(
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

    OPERATORS: Final[Tuple[str, ...]] = get_args(Operators)

    def _tokenize(self, expression: str) -> Iterator[TokenType]:
        for match in Tokenizer.GRAMMAR.finditer(expression):
            start, end = match.span()
            val = match.group()
            match match.lastgroup:
                case "number":
                    yield Number(float(val), start, end)
                case "operator" if val in Tokenizer.OPERATORS:
                    yield Operator(cast(Operators, val), start, end)
                case _:
                    yield Invalid(val, start, end)
