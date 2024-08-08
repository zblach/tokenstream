import unittest
from typing import Union

from calculator import (
    Number,
    Operator,
    Parenthesis,
    Tokenizer,
)
from tokenizer import InvalidTokenError


def tokens(expression: str) -> list[Union[str, float]]:
    return [v.value for v in Tokenizer(expression)]


class TestTokenStream(unittest.TestCase):
    def test_unary_positive(self):
        expression = "+3"
        expected_tokens = [3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_multiple_unary_positive(self):
        expression = "+3++3"
        expected_tokens = [3, "+", 3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_unary_negative(self):
        expression = "-3"
        expected_tokens = [-3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_double_negative(self):
        expression = "--3"
        expected_tokens = ["-", -3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_no_spaces_negative(self):
        expression = "4-3"
        expected_tokens = [4, "-", 3]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_no_spaces_positive(self):
        expression = "4+3"
        expected_tokens = [4, "+", 3]
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
            list(Tokenizer(expression))
        self.assertEqual(str(context.exception.token.value), "&")

    def test_empty_expression(self):
        expression = ""
        self.assertEqual(tokens(expression), [])

    def test_expression_with_whitespace(self):
        expression = "  3   + 4   * 10 -5 / 2 **  2   "
        expected_tokens = [3, "+", 4, "*", 10, "-", 5, "/", 2, "**", 2]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_expression_with_parentheses(self):
        expression = "(3 + 4) * (10 - 5)"
        expected_tokens = ["(", 3, "+", 4, ")", "*", "(", 10, "-", 5, ")"]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_parse_scientific_notation(self):
        expression = "3.2e-5 + +4.5e+6 - -1.0E100"
        expected_tokens = [3.2e-5, "+", 4.5e6, "-", -1.0e100]
        self.assertEqual(tokens(expression), expected_tokens)

    def test_typed_tokens(self):
        expression = "3 + 4 - -5 * ( 1e50 ** 0.001 )"
        expected_tokens = [
            Number(3.0, 0, 1),
            Operator("+", 2, 3),
            Number(4.0, 4, 5),
            Operator("-", 6, 7),
            Number(-5.0, 8, 10),
            Operator("*", 11, 12),
            Parenthesis("(", 13, 14),
            Number(1e50, 15, 19),
            Operator("**", 20, 22),
            Number(0.001, 23, 28),
            Parenthesis(")", 29, 30),
        ]
        self.assertEqual(list(Tokenizer(expression)), expected_tokens)
