import unittest
from calculator import evaluate
from tokenizer import (
    InvalidTokenError,
    UnexpectedEndOfExpressionError,
    UnexpectedTokenError,
)


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
        with self.assertRaises(UnexpectedTokenError):
            evaluate("(3 + 4) 3")

    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate("3 / 0")

    def test_long_invalid_token(self):
        expression = "3 + 4 $$$$$$ 10 + 5"
        with self.assertRaises(InvalidTokenError):
            evaluate(expression)

    def test_mismatched_parentheses(self):
        with self.assertRaises(UnexpectedEndOfExpressionError):
            evaluate("(3 + 4")  # Missing closing parenthesis
        with self.assertRaises(UnexpectedTokenError):
            evaluate(")3 + 4(")  # Unexpected close parenthesis
        with self.assertRaises(UnexpectedEndOfExpressionError):
            evaluate("3 + (4 * (5 - 2")  # Missing closing parenthesis
