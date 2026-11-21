#!/usr/bin/env python3
"""
strip_comments.py

Strips all comments from Forth source files and outputs the minified files
into a target directory (default: 'minified/').

Supported Forth comment styles:
  - '\\' to end-of-line comments (e.g. '\\ comment', '\\ --- Header ---')
  - '( ... )' parenthesized comments (including multiline and inline stack effects)
  - Preserves parentheses and backslashes inside Forth string literals
    (." ... ", S" ... ", C" ... ", ABORT" ... ", S\" ... \")
"""

import sys
import os
import argparse
from pathlib import Path

FORTH_EXTENSIONS = {'.f', '.fs', '.forth', '.4th', '.fth'}
IGNORED_DIRS = {'minified', 'clean', '.git', '.gemini', 'brain', 'scratch', '__pycache__', '.venv', 'env'}

def strip_forth_comments(source: str, keep_blank_lines: bool = True) -> str:
    """
    Strips Forth comments while preserving string literals and layout.
    """
    lines = source.splitlines()
    result_lines = []
    in_paren = False

    for line in lines:
        chars = []
        i = 0
        n = len(line)
        had_comment = False

        while i < n:
            if in_paren:
                if line[i] == ')':
                    in_paren = False
                    had_comment = True
                    # If followed immediately by a single space, skip it to avoid extra spacing
                    if i + 1 < n and line[i + 1] == ' ':
                        i += 1
                i += 1
                continue

            is_word_start = (i == 0 or line[i - 1].isspace())

            # Detect Forth string literals: ." , s" , c" , abort" , s\"
            str_matched = False
            for prefix in ['.\"', 's\"', 'c\"', 'abort\"', 's\\\"']:
                plen = len(prefix)
                if is_word_start and line[i:i + plen].lower() == prefix.lower():
                    if i + plen < n and line[i + plen].isspace():
                        # Append the string prefix and trailing delimiter space
                        chars.append(line[i:i + plen + 1])
                        i += plen + 1
                        escaped = False
                        while i < n:
                            c = line[i]
                            chars.append(c)
                            if prefix.lower() == 's\\\"' and c == '\\':
                                escaped = not escaped
                            elif c == '"' and not escaped:
                                i += 1
                                break
                            else:
                                escaped = False
                            i += 1
                        str_matched = True
                        break
            if str_matched:
                continue

            # Detect backslash line comments (\ followed by space, punctuation, or end of line)
            if is_word_start and line[i] == '\\':
                if i + 1 == n or line[i + 1].isspace() or line[i + 1] in '-=*#~':
                    had_comment = True
                    break  # The rest of the line is a comment

            # Detect parenthesis comments (( followed by space or end of line)
            if is_word_start and line[i] == '(':
                if i + 1 == n or line[i + 1].isspace():
                    in_paren = True
                    had_comment = True
                    i += 1
                    continue

            chars.append(line[i])
            i += 1

        cleaned = ''.join(chars).rstrip()

        # Omit lines that originally had content but became empty solely due to comments
        was_pure_comment = had_comment and not cleaned.strip() and bool(line.strip())
        if was_pure_comment:
            continue

        result_lines.append(cleaned)

    # Clean up empty lines
    final_lines = []
    blank_count = 0
    for l in result_lines:
        if not l.strip():
            if keep_blank_lines:
                if blank_count < 1:
                    final_lines.append('')
                    blank_count += 1
        else:
            blank_count = 0
            final_lines.append(l)

    # Trim leading and trailing empty lines
    while final_lines and not final_lines[0].strip():
        final_lines.pop(0)
    while final_lines and not final_lines[-1].strip():
        final_lines.pop()

    return '\n'.join(final_lines) + ('\n' if final_lines else '')


def find_source_files(root_dir: Path):
    """Recursively search for Forth files, avoiding ignored directories."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith('.')]
        for f in sorted(filenames):
            if Path(f).suffix.lower() in FORTH_EXTENSIONS:
                found.append(Path(dirpath) / f)
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Strip Forth comments (\\ and ( ... )) and save minified files in the 'minified' directory."
    )
    parser.add_argument(
        'files',
        nargs='*',
        help="Specific Forth file(s) to process. If omitted, scans the project for Forth files."
    )
    parser.add_argument(
        '-o', '--out-dir',
        default='minified',
        help="Target output directory for minified files (default: 'minified')."
    )
    parser.add_argument(
        '--no-blanks',
        action='store_true',
        help="Remove all blank lines (useful for compact serial transfer)."
    )
    parser.add_argument(
        '--preserve-tree',
        action='store_true',
        help="Preserve source sub-directory structure inside target directory."
    )
    parser.add_argument(
        '--stdout',
        action='store_true',
        help="Output minified code to stdout instead of writing to files."
    )

    args = parser.parse_args()
    root_dir = Path.cwd()
    if not (root_dir / "matrix8x8").exists() and (Path(__file__).resolve().parent.parent / "matrix8x8").exists():
        root_dir = Path(__file__).resolve().parent.parent
    out_dir = (root_dir / args.out_dir).resolve()

    if args.files:
        targets = [Path(f).resolve() for f in args.files]
    else:
        targets = find_source_files(root_dir)

    if not targets:
        print("No Forth files found to process.")
        sys.exit(0)

    if not args.stdout:
        out_dir.mkdir(parents=True, exist_ok=True)

    minified_count = 0
    for target in targets:
        if not target.is_file():
            print(f"Warning: File '{target}' not found. Skipping.", file=sys.stderr)
            continue

        try:
            with open(target, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading '{target}': {e}", file=sys.stderr)
            continue

        minified_content = strip_forth_comments(content, keep_blank_lines=not args.no_blanks)

        if args.stdout:
            sys.stdout.write(minified_content)
        else:
            if args.preserve_tree:
                try:
                    rel_path = target.relative_to(root_dir)
                    dest_file = out_dir / rel_path
                except ValueError:
                    dest_file = out_dir / target.name
            else:
                dest_file = out_dir / target.name

            dest_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(minified_content)

            try:
                display_src = target.relative_to(root_dir)
            except ValueError:
                display_src = target
            try:
                display_dest = dest_file.relative_to(root_dir)
            except ValueError:
                display_dest = dest_file

            print(f"Minified '{display_src}' -> '{display_dest}'")
            minified_count += 1

    if not args.stdout:
        print(f"\nDone! Minified {minified_count} file(s) into '{args.out_dir}/'.")


if __name__ == '__main__':
    main()
