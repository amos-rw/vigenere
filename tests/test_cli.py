import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from vigenere.cli import main

SAMPLES = Path(__file__).parent.parent / "samples"


def run(*argv, stdin=None):
    """Run the CLI and return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        if stdin is None:
            code = main(list(argv))
        else:
            with mock.patch("sys.stdin", io.StringIO(stdin)):
                code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def test_raw_message(self):
        self.assertEqual(run("HELLO", "-k", "KEY", "--raw"), (0, "RIJVS\n", ""))

    def test_words_do_not_need_quotes(self):
        code, out, _ = run("Attack", "at", "dawn!", "-k", "LEMON", "--raw")
        self.assertEqual((code, out), (0, "Lxfopv ef rnhr!\n"))

    def test_file(self):
        code, out, _ = run("-f", str(SAMPLES / "attack.txt"), "-k", "LEMON", "--raw")
        self.assertEqual((code, out), (0, "Lxfopv ef rnhr!\n"))

    def test_piped_input(self):
        self.assertEqual(run("-k", "KEY", "--raw", stdin="HELLO\n"), (0, "RIJVS\n", ""))

    def test_decrypt_message(self):
        self.assertEqual(run("RIJVS", "-k", "KEY", "-d", "--raw"), (0, "HELLO\n", ""))

    def test_decrypt_file(self):
        code, out, _ = run("-f", str(SAMPLES / "hello.enc.txt"), "-k", "KEY", "--decrypt", "--raw")
        self.assertEqual((code, out), (0, "HELLO\n"))

    def test_decrypt_result_and_steps_shown(self):
        code, out, _ = run("RIJVS", "-k", "KEY", "-d", "--steps")
        self.assertEqual(code, 0)
        for expected in ["Decrypted", "HELLO", "KEYKE", "C - K"]:
            self.assertIn(expected, out)

    def test_result_and_steps_shown(self):
        code, out, _ = run("HELLO", "-k", "KEY", "--steps")
        self.assertEqual(code, 0)
        for expected in ["RIJVS", "KEYKE", "mod 26"]:
            self.assertIn(expected, out)

    def test_output_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "out.txt"
            code, _, _ = run("HELLO", "-k", "KEY", "-o", str(target))
            self.assertEqual(code, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "RIJVS")

    def test_output_cannot_replace_the_original(self):
        source = str(SAMPLES / "hello.txt")
        code, _, err = run("-f", source, "-k", "KEY", "-o", source)
        self.assertEqual(code, 1)
        self.assertIn("overwrite", err)
        self.assertEqual(Path(source).read_text().strip(), "HELLO")

    def test_errors(self):
        for argv, stdin in [(("HELLO", "-k", "K3Y"), None),
                            (("-f", "no-such-file.txt", "-k", "KEY"), None),
                            ((), "HELLO"),
                            (("-k", "KEY"), "   ")]:
            code, out, err = run(*argv, stdin=stdin)
            self.assertEqual(code, 1, argv)
            self.assertIn("Error:", err)


if __name__ == "__main__":
    unittest.main()
