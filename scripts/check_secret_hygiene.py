#!/usr/bin/env python3
"""Fitness check offline dei permessi dei file sensibili locali presenti."""

from src.secret_hygiene import validate_runtime_secret_modes


def main() -> None:
    validate_runtime_secret_modes()
    print("Secret hygiene: OK")


if __name__ == "__main__":
    main()
