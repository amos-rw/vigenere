"""Vigenère cipher core. Pure logic: no printing, no input."""

ALPHABET_SIZE = 26


def _is_letter(ch):
    """True only for plain A-Z / a-z letters."""
    return ch.isascii() and ch.isalpha()


def validate_key(key):
    """Return the key in uppercase, or raise ValueError with a friendly message."""
    if not isinstance(key, str) or not key.strip():
        raise ValueError("The key cannot be empty.")
    key = key.strip()
    if not (key.isascii() and key.isalpha()):
        raise ValueError("The key must contain letters A-Z only.")
    return key.upper()


def key_stream(text, key):
    """One entry per character of text: the key letter for letters, None for the rest.

    The key only advances on letters, so spaces and punctuation never use it up.
    """
    key = validate_key(key)
    stream, i = [], 0
    for ch in text:
        if _is_letter(ch):
            stream.append(key[i % len(key)])
            i += 1
        else:
            stream.append(None)
    return stream


def _shift_char(ch, k):
    base = ord("A") if ch.isupper() else ord("a")
    return chr((ord(ch) - base + k) % ALPHABET_SIZE + base)


def _apply(text, key, sign):
    out = []
    for ch, k in zip(text, key_stream(text, key)):
        out.append(ch if k is None else _shift_char(ch, sign * (ord(k) - ord("A"))))
    return "".join(out)


def encrypt(text, key):
    """C = (P + K) mod 26. Keeps case; leaves non-letters untouched."""
    return _apply(text, key, 1)


def decrypt(text, key):
    """P = (C - K) mod 26. The exact reverse of encrypt."""
    return _apply(text, key, -1)


def steps(text, key, decrypting=False):
    """Letter-by-letter breakdown as a list of dicts (letters only).

    "p" is the number of the letter going in: plain when encrypting, cipher when decrypting.
    """
    sign = -1 if decrypting else 1
    rows = []
    for ch, k in zip(text, key_stream(text, key)):
        if k is None:
            continue
        p = ord(ch.upper()) - ord("A")
        kv = ord(k) - ord("A")
        raw = p + sign * kv
        res = raw % ALPHABET_SIZE
        rows.append({
            "letter": ch.upper(), "p": p,
            "key": k, "k": kv, "op": "-" if decrypting else "+",
            "raw": raw, "n": res, "result": chr(res + ord("A")),
        })
    return rows


def format_step(row):
    """One short line, e.g. 'H (7) + K (10) = 17 → R'."""
    line = f"{row['letter']} ({row['p']}) {row['op']} {row['key']} ({row['k']}) = {row['raw']}"
    if row["raw"] != row["n"]:
        line += f", wraps to {row['n']}"
    return f"{line} → {row['result']}"
