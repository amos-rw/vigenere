import unittest

from vigenere.tools import (alphabet_table, letter_to_number,
                            number_to_letter)


class TestTools(unittest.TestCase):
    def test_alphabet_table(self):
        table = alphabet_table()
        self.assertEqual(len(table), 26)
        self.assertEqual(table[0], ("A", 0))
        self.assertEqual(table[-1], ("Z", 25))

    def test_letter_and_number(self):
        self.assertEqual(letter_to_number("c"), 2)
        self.assertEqual(number_to_letter(17), "R")
        self.assertEqual(number_to_letter(-1), "Z")

    def test_bad_letter(self):
        for bad in ["", "AB", "5", "é"]:
            with self.assertRaises(ValueError):
                letter_to_number(bad)


if __name__ == "__main__":
    unittest.main()
