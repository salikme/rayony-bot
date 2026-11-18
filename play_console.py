# -*- coding: utf-8 -*-
"""Играть в консоли без Telegram: python play_console.py"""
import html
import re

from engine import Game


def plain(t):
    return html.unescape(re.sub(r"</?[bi]>", "", t))


def main():
    g = Game()
    while True:
        text, btns = g.view()
        print("\n" + plain(text) + "\n")
        for i, b in enumerate(btns, 1):
            print(f"  {i}. {plain(b)}")
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if raw.lower() in ("q", "выход"):
            break
        if raw.isdigit() and 1 <= int(raw) <= len(btns):
            g.choose(int(raw) - 1)


if __name__ == "__main__":
    main()
