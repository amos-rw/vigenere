import unittest

from vigenere.cipher import (decrypt, encrypt, format_step, key_stream, steps,
                             validate_key)


class TestEncrypt(unittest.TestCase):
    def test_hello_key(self):
        self.assertEqual(encrypt("HELLO", "KEY"), "RIJVS")

    def test_case_and_punctuation_kept(self):
        self.assertEqual(encrypt("Attack at dawn!", "LEMON"), "Lxfopv ef rnhr!")

    def test_key_case_does_not_matter(self):
        self.assertEqual(encrypt("HELLO", "key"), encrypt("HELLO", "KEY"))

    def test_non_ascii_letters_untouched(self):
        self.assertEqual(encrypt("café", "A"), "café")

    def test_empty_text(self):
        self.assertEqual(encrypt("", "KEY"), "")


class TestDecrypt(unittest.TestCase):
    def test_hello_key(self):
        self.assertEqual(decrypt("RIJVS", "KEY"), "HELLO")

    def test_case_and_punctuation_kept(self):
        self.assertEqual(decrypt("Lxfopv ef rnhr!", "LEMON"), "Attack at dawn!")

    def test_round_trip(self):
        text = "The quick brown fox, 123 times: jumps over the lazy dog?"
        for key in ["A", "Z", "KEY", "LEMON"]:
            self.assertEqual(decrypt(encrypt(text, key), key), text)


class TestKey(unittest.TestCase):
    def test_bad_keys(self):
        for bad in ["", "   ", "K3Y", "KE Y", "é", None]:
            with self.assertRaises(ValueError):
                validate_key(bad)

    def test_key_waits_on_non_letters(self):
        self.assertEqual(key_stream("A B", "XY"), ["X", None, "Y"])


class TestSteps(unittest.TestCase):
    def test_first_step_text(self):
        self.assertEqual(format_step(steps("HELLO", "KEY")[0]), "H (7) + K (10) = 17 → R")

    def test_wrap_on_encrypt(self):
        self.assertEqual(format_step(steps("HELLO", "KEY")[2]),
                         "L (11) + Y (24) = 35, wraps to 9 → J")

    def test_first_step_text_on_decrypt(self):
        self.assertEqual(format_step(steps("RIJVS", "KEY", decrypting=True)[0]),
                         "R (17) - K (10) = 7 → H")

    def test_wrap_on_decrypt(self):
        self.assertEqual(format_step(steps("RIJVS", "KEY", decrypting=True)[2]),
                         "J (9) - Y (24) = -15, wraps to 11 → L")

    def test_steps_skip_non_letters(self):
        self.assertEqual(len(steps("a, b!", "K")), 2)


if __name__ == "__main__":
    unittest.main()
