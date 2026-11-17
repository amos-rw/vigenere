"""Command-line interface. The only module that prints or asks for input."""

import argparse
import sys
from pathlib import Path

from rich import box
from rich.cells import cell_len
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from vigenere.cipher import decrypt, encrypt, key_stream, steps, validate_key
from vigenere.tools import (DECRYPT_FORMULA, FORMULA, FORMULA_NOTES,
                            alphabet_table, letter_to_number, number_to_letter)

STEP_LIMIT = 30  # most letters shown by the steps table

EXAMPLES = """examples:
  python -m vigenere                               open the menu
  python -m vigenere HELLO -k KEY                  encrypt a message
  python -m vigenere RIJVS -k KEY -d               decrypt it again
  python -m vigenere Attack at dawn! -k LEMON -s   show every step
  python -m vigenere -f samples/hello.txt -k KEY -o hello.enc.txt
  python -m vigenere --table --formula
"""

MENU = [
    ("1", "Encrypt a message"),
    ("2", "Encrypt a file"),
    ("3", "Decrypt a message"),
    ("4", "Decrypt a file"),
    ("5", "Alphabet table"),
    ("6", "Formula"),
    ("q", "Quit"),
]

console = Console(highlight=False)
err = Console(stderr=True, highlight=False)


# ---- Files ---------------------------------------------------------------
def read_text(path):
    """File contents as text, or ValueError with a friendly message."""
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except UnicodeDecodeError:
        raise ValueError(f"{path} is not a UTF-8 text file.")
    except OSError as e:
        raise ValueError(f"Cannot read {path}: {e.strerror}")


def save_text(path, text, source=None):
    """Write text to path. Refuses to overwrite the file it was read from."""
    if source and Path(path).resolve() == Path(source).resolve():
        raise ValueError("That would overwrite the original file. Pick another name.")
    try:
        Path(path).write_text(text, encoding="utf-8")
    except OSError as e:
        raise ValueError(f"Cannot write {path}: {e.strerror}")
    console.print(Text.assemble(("Saved to ", "dim"), str(path)))


# ---- Screens -------------------------------------------------------------
def show_result(text, key, result, decrypting=False):
    before, after = text.rstrip("\n"), result.rstrip("\n")
    # A short one-line message gets its key letters lined up underneath it.
    lined_up = (before.isprintable() and cell_len(before) == len(before)
                and len(before) <= console.width - 16)
    key_line = "".join(k or " " for k in key_stream(before, key)) if lined_up else ""
    key_line = key_line if key_line.strip() else key

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim", no_wrap=True)
    grid.add_column()
    grid.add_row("Cipher" if decrypting else "Message", Text(before))
    grid.add_row("Key", Text(key_line, style="cyan"))
    grid.add_row("Message" if decrypting else "Cipher", Text(after, style="bold green"))
    console.print(Panel(grid, title="Decrypted" if decrypting else "Encrypted",
                        title_align="left", border_style="green", expand=False))
    if after == before:
        console.print("[yellow]Nothing changed: the message has no letters A-Z, "
                      "or the key is all A's.[/]")


def show_steps(text, key, decrypting=False):
    rows = steps(text, key, decrypting)
    if not rows:
        return
    names = (("#", "Cipher", "C", "Key", "K", "C - K", "mod 26", "Plain") if decrypting
             else ("#", "Plain", "P", "Key", "K", "P + K", "mod 26", "Cipher"))
    table = Table(title="Letter by letter", title_justify="left", box=box.ROUNDED)
    for name in names:
        table.add_column(name, justify="center" if name in ("Plain", "Key", "Cipher") else "right")
    for n, r in enumerate(rows[:STEP_LIMIT], 1):
        wrapped = r["raw"] != r["n"]
        table.add_row(str(n), r["letter"], str(r["p"]), Text(r["key"], style="cyan"),
                      str(r["k"]), str(r["raw"]),
                      Text(str(r["n"]), style="yellow" if wrapped else ""),
                      Text(r["result"], style="bold green"))
    if len(rows) > STEP_LIMIT:
        table.caption = f"First {STEP_LIMIT} of {len(rows)} letters."
    console.print(table)


def show_table():
    pairs = alphabet_table()
    half = len(pairs) // 2
    table = Table(title="Alphabet to number", title_justify="left",
                  show_header=False, box=box.ROUNDED)
    for _ in range(half):
        table.add_column(justify="center")
    for chunk in (pairs[:half], pairs[half:]):
        table.add_row(*[Text(letter, style="bold cyan") for letter, _ in chunk])
        table.add_row(*[str(n) for _, n in chunk], end_section=True)
    console.print(table)


def show_formula():
    body = Text(f"{FORMULA}\n{DECRYPT_FORMULA}\n", style="bold green")
    for note in FORMULA_NOTES:
        body.append(f"\n{note}", style="default")
    console.print(Panel(body, title="Formula", title_align="left", expand=False))


# ---- Menu ----------------------------------------------------------------
def ask_key(default=None):
    """Keep asking until the key is valid."""
    while True:
        try:
            return validate_key(Prompt.ask("Key", default=default))
        except ValueError as e:
            console.print(f"[red]{e}[/]")


def convert_loop():
    """AlphabetToNum: type a letter to get its number, or a number to get its letter."""
    while True:
        entry = Prompt.ask("Letter or number to convert [dim](Enter to go back)[/]",
                           default="", show_default=False)
        if not entry:
            return
        try:
            if entry.lstrip("-").isdecimal():
                answer = number_to_letter(int(entry))
            else:
                answer = letter_to_number(entry)
            console.print(f"  {escape(entry.upper())} → [bold cyan]{answer}[/]")
        except ValueError as e:
            console.print(f"  [red]{e}[/]")


def convert(text, key, decrypting=False):
    """Encrypt or decrypt, refusing a blank message."""
    if not text.strip():
        raise ValueError(f"There is no message to {'decrypt' if decrypting else 'encrypt'}.")
    return (decrypt if decrypting else encrypt)(text, key)


def menu():
    console.print(Panel(Text.assemble(("Vigenère Cipher", "bold"),
                                      ("  encrypt and decrypt\n", "dim"),
                                      ("\nDone By Amos & Manzi", "green"),
                                      (f"\n\n{FORMULA}\n{DECRYPT_FORMULA}", "cyan")),
                        border_style="cyan", expand=False, padding=(0, 2)))
    last_key = None
    while True:
        console.print()
        for choice, label in MENU:
            console.print(f"  [bold cyan]{choice}[/]  {label}")
        choice = Prompt.ask("Choose", choices=[c for c, _ in MENU], default="1",
                            case_sensitive=False).lower()
        decrypting = choice in ("3", "4")
        try:
            if choice in ("1", "3"):
                text = Prompt.ask("Ciphertext" if decrypting else "Message",
                                  default="", show_default=False)
                convert(text, "A", decrypting)  # complain about an empty message before asking for a key
                last_key = ask_key(last_key)
                show_result(text, last_key, convert(text, last_key, decrypting), decrypting)
                show_steps(text, last_key, decrypting)
            elif choice in ("2", "4"):
                sample = "samples/hello.enc.txt" if decrypting else "samples/hello.txt"
                path = Prompt.ask("File", default=sample).strip('"')
                text = read_text(path)
                last_key = ask_key(last_key)
                result = convert(text, last_key, decrypting)
                show_result(text, last_key, result, decrypting)
                out = Prompt.ask("Save as [dim](Enter to skip)[/]",
                                 default="", show_default=False).strip('"')
                if out:
                    save_text(out, result, source=path)
            elif choice == "5":
                show_table()
                convert_loop()
            elif choice == "6":
                show_formula()
            else:
                return 0
        except ValueError as e:
            console.print(Text(str(e), style="red"))


# ---- Command line --------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m vigenere",
        description="Encrypt or decrypt text with the Vigenère cipher. "
                    "Run with no arguments for the menu.",
        epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("text", nargs="*", help="the message to encrypt, or to decrypt with -d")
    parser.add_argument("-k", "--key", help="the key, letters A-Z only")
    parser.add_argument("-d", "--decrypt", action="store_true", help="decrypt instead of encrypt")
    parser.add_argument("-f", "--file", help="use this text file instead of a message")
    parser.add_argument("-o", "--output", help="also save the result to this file")
    parser.add_argument("-s", "--steps", action="store_true", help="show the work for every letter")
    parser.add_argument("-t", "--table", action="store_true", help="show the alphabet table (A=0 ... Z=25)")
    parser.add_argument("--formula", action="store_true", help="show the formulas")
    parser.add_argument("-r", "--raw", action="store_true",
                        help="print only the result, for piping into other commands")
    return parser


def run(args, interactive):
    if args.table:
        show_table()
    if args.formula:
        show_formula()
    if (args.table or args.formula) and not (args.text or args.file or args.key):
        return 0

    if args.text and args.file:
        raise ValueError("Give a message or --file, not both.")
    if args.file:
        text = read_text(args.file)
    elif args.text:
        text = " ".join(args.text)
    elif interactive:
        text = Prompt.ask("Message", default="")
    else:
        text = sys.stdin.read()

    if args.key:
        key = validate_key(args.key)
    elif interactive:
        key = ask_key()
    else:
        raise ValueError("A key is needed. Add: -k KEY")

    result = convert(text, key, args.decrypt)
    if args.raw:
        sys.stdout.write(result if result.endswith("\n") else result + "\n")
    else:
        show_result(text, key, result, args.decrypt)
        if args.steps:
            show_steps(text, key, args.decrypt)
    if args.output:
        save_text(args.output, result, source=args.file)
    return 0


def main(argv=None):
    # Windows consoles and redirected output default to a codepage without "→".
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else argv
    interactive = sys.stdin.isatty()
    try:
        if not argv and interactive:
            return menu()
        return run(build_parser().parse_args(argv), interactive)
    except ValueError as e:
        err.print(Text.assemble(("Error: ", "bold red"), str(e)))
        return 1
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Bye.[/]")
        return 130
