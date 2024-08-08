import unittest
from calculator.tokenizer import UnexpectedEndOfExpressionError
from rpn import evaluate
from tokenizer import InvalidTokenError, UnexpectedTokenError


class TestRPNCalculator(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(evaluate("2 3 +"), 5)
        self.assertEqual(evaluate("10 5 +"), 15)
        self.assertEqual(evaluate("0 0 +"), 0)

    def test_subtraction(self):
        self.assertEqual(evaluate("5 3 -"), 2)
        self.assertEqual(evaluate("10 5 -"), 5)
        self.assertEqual(evaluate("0 0 -"), 0)

    def test_multiplication(self):
        self.assertEqual(evaluate("2 3 *"), 6)
        self.assertEqual(evaluate("10 5 *"), 50)
        self.assertEqual(evaluate("0 0 *"), 0)

    def test_division(self):
        self.assertEqual(evaluate("6 3 /"), 2)
        self.assertEqual(evaluate("10 5 /"), 2)
        self.assertEqual(evaluate("0 5 /"), 0)

    def test_complex_expression(self):
        self.assertEqual(evaluate("2 3 + 4 *"), 20)
        self.assertEqual(evaluate("10 5 - 2 *"), 10)
        self.assertEqual(evaluate("6 3 / 2 +"), 4)

    def test_too_many_tokens(self):
        self.assertRaises(UnexpectedEndOfExpressionError, evaluate, "1 2 3 + 4 * 5")
        self.assertRaises(UnexpectedEndOfExpressionError, evaluate, "10 5 - 2 * 3 2 /")
        self.assertRaises(UnexpectedEndOfExpressionError, evaluate, "4 2 1-")

    def test_insufficient_tokens(self):
        self.assertRaises(UnexpectedTokenError, evaluate, "2 +")
        self.assertRaises(UnexpectedTokenError, evaluate, "10 4 - *")
        self.assertRaises(UnexpectedTokenError, evaluate, "/")

    def test_illegal_tokens(self):
        self.assertRaises(InvalidTokenError, evaluate, "2 3 + a")
        self.assertRaises(InvalidTokenError, evaluate, "10 5 - 2 * bbbbb 3 2 /")
