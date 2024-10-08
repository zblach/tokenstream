import unittest
from typing import Union

from calculator.tokenizer import Operator, Parenthesis, Tokenizer
from tokenizer import Invalid, Number


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
        tokens = list(Tokenizer(expression))
        self.assertIsInstance(tokens[3], Invalid)

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
        expression = "-3 + 4 - -5 * abcde (  1e50 ** 0.001)"
        expected_token_types_and_values = [
            (Number, -3.0),
            (Operator, "+"),
            (Number, 4.0),
            (Operator, "-"),
            (Number, -5.0),
            (Operator, "*"),
            (Invalid, "abcde"),
            (Parenthesis, "("),
            (Number, 1e50),
            (Operator, "**"),
            (Number, 0.001),
            (Parenthesis, ")"),
        ]
        actual_tokens = list(Tokenizer(expression))
        self.assertEqual(
            [(type(token), token.value) for token in actual_tokens],
            expected_token_types_and_values,
        )
