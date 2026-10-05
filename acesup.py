"""Aces Up solitaire in the terminal. Pure stdlib."""

import argparse
import random
import secrets
import sys

SUITS = ("♠", "♥", "♦", "♣")
RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
RANK_VALUE = {r: i for i, r in enumerate(RANKS)}


def new_deck():
    return [(r, s) for s in SUITS for r in RANKS]


def card_name(card):
    return f"{card[1]}{card[0]}"


class Game:
    def __init__(self, seed=None):
        rng = random.Random(seed) if seed is not None else secrets.SystemRandom()
        self.deck = new_deck()
        rng.shuffle(self.deck)
        self.piles = [[], [], [], []]
        self.moves = 0

    def tops(self):
        return [p[-1] if p else None for p in self.piles]

    def deal(self):
        """Deal one card to each non-empty-capable pile; False when deck empty."""
        if not self.deck:
            return False
        for p in self.piles:
            if self.deck:
                p.append(self.deck.pop())
        return True

    def discards(self):
        """All (pile_index) cards that can be discarded: lower card of a same-suit pair.

        Rules: A is high and never discarded; only the top card of each pile
        is considered; a card is discarded if another pile's top card has the
        same suit and a higher rank.
        """
        tops = self.tops()
        out = []
        for i, card in enumerate(tops):
            if card is None or card[0] == "A":
                continue
            for j, other in enumerate(tops):
                if i != j and other is not None and other[1] == card[1] \
                        and RANK_VALUE[other[0]] > RANK_VALUE[card[0]]:
                    out.append(i)
                    break
        return out

    def discard(self, i):
        tops = self.tops()
        card = tops[i]
        if card is None or card[0] == "A":
            return False
        for j, other in enumerate(tops):
            if i != j and other is not None and other[1] == card[1] \
                    and RANK_VALUE[other[0]] > RANK_VALUE[card[0]]:
                self.piles[i].pop()
                self.moves += 1
                return True
        return False

    def move_ace_to_empty(self, i):
        """Move an ace from pile i to an empty pile; False if not applicable."""
        tops = self.tops()
        card = tops[i]
        if card is None or card[0] != "A":
            return False
        for j, p in enumerate(self.piles):
            if j != i and not p:
                p.append(self.piles[i].pop())
                self.moves += 1
                return True
        return False

    def won(self):
        remaining = [c for p in self.piles for c in p]
        return (not self.deck and len(remaining) == 4
                and all(c[0] == "A" for c in remaining))

    def stuck(self):
        if self.deck or self.discards():
            return False
        if any(not p for p in self.piles):
            return not any(t is not None and t[0] == "A" for t in self.tops())
        return True


def render(g):
    lines = [f"牌堆剩: {len(g.deck)}   步数: {g.moves}"]
    tops = g.tops()
    lines.append("  ".join(card_name(t) if t else "[空]" for t in tops))
    lines.append("   1     2     3     4")
    return "\n".join(lines)


def auto_play(seed=None, verbose=False):
    g = Game(seed)
    g.deal()
    moved_aces = set()  # id() of ace cards already relocated (prevents ping-pong)
    while True:
        did = False
        for i in g.discards():
            g.discard(i)
            did = True
        if not did:
            for i, t in enumerate(g.tops()):
                if t is not None and t[0] == "A" and id(t) not in moved_aces \
                        and g.move_ace_to_empty(i):
                    moved_aces.add(id(t))
                    did = True
                    break
        if not did:
            if not g.deal():
                break
    if verbose:
        print(render(g))
    return g


def play_interactive(seed=None):
    if not sys.stdin.isatty():
        print("error: 交互模式需要终端, 管道请用 --auto", file=sys.stderr)
        sys.exit(2)
    g = Game(seed)
    g.deal()
    print("Aces Up: 4 堆, 每轮发 1 张; 同花色丢小牌(保留大牌), A 永不丢; A 可移到空堆。")
    print("命令: d 发牌 | x <堆号> 丢牌 | m <堆号> 移A到空堆 | q 退出")
    while True:
        print(render(g))
        if g.won():
            print("🎉 胜利! 只剩 4 张 A。")
            return
        if g.stuck():
            print("😞 卡死了, 无牌可走。")
            return
        try:
            raw = input("> ").strip().split()
        except EOFError:
            print()
            return
        if not raw:
            continue
        cmd = raw[0].lower()
        if cmd == "q":
            return
        if cmd == "d":
            if not g.deal():
                print("牌堆已空。")
            continue
        if cmd == "x" and len(raw) == 2 and raw[1] in "1234":
            if g.discard(int(raw[1]) - 1):
                print("已丢牌。")
            else:
                print("这张牌现在不能丢。")
            continue
        if cmd == "m" and len(raw) == 2 and raw[1] in "1234":
            if g.move_ace_to_empty(int(raw[1]) - 1):
                print("A 已移到空堆。")
            else:
                print("无法移动(不是 A 或没有空堆)。")
            continue
        print("未知命令。")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Aces Up 纸牌接龙")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--auto", action="store_true", help="自动游玩一局")
    args = ap.parse_args(argv)
    if args.auto:
        g = auto_play(args.seed, verbose=True)
        print("胜利!" if g.won() else "失败。")
    else:
        play_interactive(args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
