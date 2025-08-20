#!/usr/bin/env python3
"""
***Austin's Blackjack Trainer — Perfect Basic Strategy + Hi-Lo Count + Bet Hints***
- Multi-deck basic strategy (pairs, soft & hard totals)
- Rule toggles: S17/H17, Late Surrender (LS), Double After Split (DAS), Double 11 vs Ace
- Counting: running count (Hi-Lo), true count (decks remaining from cards you've marked as seen)
- Betting: simple, configurable bet ramp with "Max bet" hint
- CLI helpers: set rules, set decks, add/remove seen cards, shuffle, show count, help

NOTE: This is a practice/training tool.. Use responsibly and follow venue rules/ToS.
"""

from typing import List, Tuple
import sys

# ---------- DEFAULT TABLE RULES ----------
H17 = False                # Dealer hits soft 17? (False -> S17 default)
LATE_SURRENDER = True      # Late surrender available?
DAS = True                 # Double after split allowed?
DOUBLE_11_VS_ACE = False   # Double 11 vs Ace on two cards?

# Edge preferences for 8,8 surrender (optional; keep defaults unless you know your table)
SURRENDER_88_VS_T = True
SURRENDER_88_VS_A_H17 = True
SURRENDER_88_VS_A_S17 = False

# ---------- COUNTING / BETTING ----------
DEFAULT_NUM_DECKS = 6

# Bet ramp style: 'conservative' | 'standard' | 'aggressive'
BET_STYLE = "standard"
# Maximum recommended units when ramp tops out (you can map units to chip size privately)
BET_MAX_UNITS = 8

# Hi-Lo tags (use "T" for 10/J/Q/K)
HI_LO = {
    "2":  +1, "3":  +1, "4":  +1, "5":  +1, "6":  +1,
    "7":   0, "8":   0, "9":   0,
    "T":  -1, "A":  -1,
}

# ---------- CARD PARSING ----------
DIGITS = set("23456789")
VALID_RANKS = {"2","3","4","5","6","7","8","9","T","J","Q","K","A"}
DISPLAY_UP = {"T":"T","J":"T","Q":"T","K":"T","A":"A",
              "2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9"}

def normalize_card(c: str) -> str:
    c = c.strip().upper()
    if c in {"10","T","J","Q","K"}: return "T"
    if c in DIGITS or c == "A": return c
    raise ValueError(f"Invalid card: {c}")

def parse_upcard(s: str) -> str:
    return DISPLAY_UP[normalize_card(s)]

def tokenize_cards(s: str) -> List[str]:
    """
    Accepts: 'A,7', 'A-7', 'A7', 'AT', 'T,6,3', '8 8', '10,J'
    Splits on any non-rank character; compacts 10/J/Q/K to 'T'.
    """
    s = s.strip().upper().replace("10", "T")
    out = []
    for ch in s:
        if ch in {"A","K","Q","J","T"} or ch in DIGITS:
            out.append(ch)
        else:
            # treat everything else as a separator
            out.append(" ")
    parts = [p for p in "".join(out).split() if p]
    # Flatten sequences like "AT" -> ["A","T"]
    flat: List[str] = []
    for p in parts:
        for ch in p:
            flat.append(ch)
    return [normalize_card(x) for x in flat]

def parse_hand(text: str) -> List[str]:
    cards = tokenize_cards(text)
    if not cards:
        raise ValueError("Empty hand.")
    for c in cards:
        if c not in {"2","3","4","5","6","7","8","9","T","A"}:
            raise ValueError(f"Invalid rank in hand: {c}")
    return cards

# ---------- HAND EVALUATION ----------
def hand_total_and_soft(cards: List[str]) -> Tuple[int, bool, int]:
    """Return (total, soft_flag, soft_aces_counted_as_11)."""
    total, aces = 0, 0
    for c in cards:
        if c == "A":
            total += 11
            aces += 1
        elif c == "T":
            total += 10
        else:
            total += int(c)
    soft_aces = aces
    while total > 21 and soft_aces > 0:
        total -= 10
        soft_aces -= 1
    return total, (soft_aces > 0), soft_aces

def is_pair(cards: List[str]) -> bool:
    return len(cards) == 2 and cards[0] == cards[1]

# ---------- STRATEGY ENGINE ----------
def maybe_surrender(default_move: str, first_two: bool) -> str:
    if LATE_SURRENDER and first_two:
        return f"Surrender (otherwise {default_move})"
    return default_move

def advise(hand_cards: List[str], dealer_up: str, first_two: bool = True) -> str:
    """
    Returns: 'Hit', 'Stand', 'Double', 'Split', or 'Surrender (otherwise X)'
    Strategy: multi-deck with options above.
    """
    total, soft, _ = hand_total_and_soft(hand_cards)
    dealer = parse_upcard(dealer_up)

    # Pairs (first decision only)
    if first_two and is_pair(hand_cards):
        r = hand_cards[0]
        if r == "A": return "Split"
        if r == "T": return "Stand"
        if r == "9":
            return "Split" if dealer in {"2","3","4","5","6","8","9"} else "Stand"
        if r == "8":
            if dealer == "T" and SURRENDER_88_VS_T:
                return maybe_surrender("Split", first_two=True)
            if dealer == "A":
                if (H17 and SURRENDER_88_VS_A_H17) or (not H17 and SURRENDER_88_VS_A_S17):
                    return maybe_surrender("Split", first_two=True)
            return "Split"
        if r == "7":
            return "Split" if dealer in {"2","3","4","5","6","7"} else "Hit"
        if r == "6":
            return "Split" if dealer in {"2","3","4","5","6"} else "Hit"
        if r == "5":
            return "Double" if dealer in {"2","3","4","5","6","7","8","9"} else "Hit"
        if r == "4":
            if DAS and dealer in {"5","6"}: return "Split"
            return "Hit"
        if r in {"2","3"}:
            if DAS and dealer in {"2","3","4","5","6","7"}: return "Split"
            if not DAS and dealer in {"4","5","6","7"}: return "Split"
            return "Hit"

    # Soft totals
    if soft:
        if total >= 20: return "Stand"
        if total == 19:
            if H17 and dealer == "6": return "Double" if first_two else "Stand"
            return "Stand"
        if total == 18:
            if dealer in {"3","4","5","6"}: return "Double" if first_two else "Stand"
            if H17 and dealer == "2": return "Double" if first_two else "Stand"
            if dealer in {"2","7","8"}: return "Stand"
            return "Hit"  # vs 9,T,A
        if total == 17:
            return "Double" if first_two and dealer in {"3","4","5","6"} else "Hit"
        if total in {15,16}:
            return "Double" if first_two and dealer in {"4","5","6"} else "Hit"
        if total in {13,14}:
            return "Double" if first_two and dealer in {"5","6"} else "Hit"
        return "Hit"

    # Hard totals
    if total >= 17: return "Stand"

    if total == 16:
        if dealer in {"9","T","A"} and first_two:
            return maybe_surrender("Hit", first_two=True)
        return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"

    if total == 15:
        if first_two:
            if dealer == "T": return maybe_surrender("Hit", first_two=True)
            if H17 and dealer == "9": return maybe_surrender("Hit", first_two=True)
        return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"

    if total in {13,14}:
        return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"

    if total == 12:
        return "Stand" if dealer in {"4","5","6"} else "Hit"

    if total == 11:
        if dealer == "A":
            return "Double" if (DOUBLE_11_VS_ACE and first_two) else "Hit"
        return "Double" if first_two else "Hit"

    if total == 10:
        return "Double" if first_two and dealer in {"2","3","4","5","6","7","8","9"} else "Hit"

    if total == 9:
        return "Double" if first_two and dealer in {"3","4","5","6"} else "Hit"

    return "Hit"  # 8 or less

# ---------- COUNT TRACKER ----------
class CountTracker:
    def __init__(self, num_decks: int = DEFAULT_NUM_DECKS):
        self.reset(num_decks)

    def reset(self, num_decks: int = None):
        if num_decks is not None:
            if not (1 <= num_decks <= 8):
                raise ValueError("Decks must be between 1 and 8.")
            self.num_decks = int(num_decks)
        self.running = 0
        self.seen = 0
        self._history: List[List[str]] = []

    def add_seen(self, cards: List[str]):
        """Add a batch of seen cards and push to history (for undo)."""
        batch = [normalize_card(c) for c in cards]
        for c in batch:
            if c in HI_LO:
                self.running += HI_LO[c]
            self.seen += 1
        self._history.append(batch)

    def undo(self) -> bool:
        if not self._history: return False
        last = self._history.pop()
        for c in last:
            if c in HI_LO:
                self.running -= HI_LO[c]
            self.seen -= 1
        if self.seen < 0: self.seen = 0
        return True

    @property
    def decks_remaining(self) -> float:
        total_cards = self.num_decks * 52
        remaining = max(0, total_cards - self.seen)
        return remaining / 52.0

    @property
    def true_count(self) -> float:
        denom = max(0.25, self.decks_remaining)  # avoid divide-by-near-zero
        return self.running / denom

# ---------- BET RAMP ----------
def bet_units_from_true_count(tc: float, style: str = BET_STYLE, max_units: int = BET_MAX_UNITS) -> int:
    """
    Map true count to betting units. Tweak to your taste.
    - conservative: TC<=0:1u, 1:1u, 2:2u, 3:3u, 4:4u, >=5:max
    - standard:     TC<=0:1u, 1:2u, 2:4u, 3:6u, 4:6u, >=5:max
    - aggressive:   TC<=-1:1u, 0:2u, 1:3u, 2:5u, 3:7u, >=4:max
    """
    t = int(tc)
    if style == "conservative":
        if t <= 0: return 1
        if t == 1: return 1
        if t == 2: return 2
        if t == 3: return 3
        if t == 4: return 4
        return max_units
    elif style == "aggressive":
        if t <= -1: return 1
        if t == 0: return 2
        if t == 1: return 3
        if t == 2: return 5
        if t == 3: return 7
        return max_units
    # standard
    if t <= 0: return 1
    if t == 1: return 2
    if t == 2: return 4
    if t in {3,4}: return 6
    return max_units

def bet_advice(tc: float, style: str = BET_STYLE, max_units: int = BET_MAX_UNITS) -> str:
    units = bet_units_from_true_count(tc, style, max_units)
    if units >= max_units:
        return f"MAX bet → {units} units"
    if units == 1:
        return "Minimum bet → 1 unit"
    return f"Increase bet → {units} units"

# ---------- CLI ----------
HELP = """
Commands:
  help                     Show this help
  rules                    Show current rule & bet settings
  set h17 on|off           Dealer hits soft 17
  set ls on|off            Late surrender
  set das on|off           Double after split
  set d11a on|off          Double 11 vs Ace
  set s88t on|off          8,8 vs 10 surrender edge
  set s88a_h17 on|off      8,8 vs A surrender (H17)
  set s88a_s17 on|off      8,8 vs A surrender (S17)

  decks N                  Set shoe size to N decks (resets count)
  shuffle                  Reset running count and seen cards
  count                    Show running count, true count, and decks remaining
  seen <cards>             Add arbitrary seen cards (e.g., seen 7,3,T,A,9)
  undo                     Undo the last 'seen' batch
  betstyle s|c|a           Set bet ramp: standard | conservative | aggressive
  betmax N                 Set max bet units (default 8)
  quit / exit              Leave program

Usage:
  1) Enter your hand and dealer upcard to get the perfect move.
  2) Then enter which cards were SEEN this round:
       - Press Enter to count just your hand + dealer upcard, or
       - Type every exposed card at the table for better accuracy.
"""

def print_rules(counter: CountTracker):
    print("\nCurrent Rules / Settings:")
    print(f"  Dealer: {'H17 (hits soft 17)' if H17 else 'S17 (stands on soft 17)'}")
    print(f"  Late Surrender: {'On' if LATE_SURRENDER else 'Off'}")
    print(f"  Double After Split (DAS): {'On' if DAS else 'Off'}")
    print(f"  Double 11 vs Ace: {'On' if DOUBLE_11_VS_ACE else 'Off'}")
    print(f"  8,8 vs T Surrender: {'On' if SURRENDER_88_VS_T else 'Off'}")
    print(f"  8,8 vs A Surrender (H17): {'On' if SURRENDER_88_VS_A_H17 else 'Off'}")
    print(f"  8,8 vs A Surrender (S17): {'On' if SURRENDER_88_VS_A_S17 else 'Off'}")
    print(f"  Decks in shoe: {counter.num_decks}")
    print(f"  Bet ramp: {BET_STYLE} (max units={BET_MAX_UNITS})")
    print(f"  Count → running: {counter.running:+d}, true: {counter.true_count:+.2f}, decks remaining: {counter.decks_remaining:.2f}\n")

def set_option(parts: List[str], counter: CountTracker):
    global H17, LATE_SURRENDER, DAS, DOUBLE_11_VS_ACE
    global SURRENDER_88_VS_T, SURRENDER_88_VS_A_H17, SURRENDER_88_VS_A_S17
    global BET_STYLE, BET_MAX_UNITS

    if not parts:
        print("Type 'help' for commands.")
        return

    cmd = parts[0].lower()

    if cmd == "set" and len(parts) >= 3:
        key, val = parts[1].lower(), parts[2].lower()
        if val not in {"on","off"}:
            print("Value must be 'on' or 'off'.")
            return
        flag = (val == "on")
        if key == "h17": H17 = flag
        elif key == "ls": LATE_SURRENDER = flag
        elif key == "das": DAS = flag
        elif key == "d11a": DOUBLE_11_VS_ACE = flag
        elif key == "s88t": SURRENDER_88_VS_T = flag
        elif key == "s88a_h17": SURRENDER_88_VS_A_H17 = flag
        elif key == "s88a_s17": SURRENDER_88_VS_A_S17 = flag
        else:
            print("Unknown option. Try: h17, ls, das, d11a, s88t, s88a_h17, s88a_s17")
            return
        print_rules(counter)
        return

    if cmd == "betstyle" and len(parts) >= 2:
        style = parts[1].lower()
        if style in {"standard","s"}: BET_STYLE = "standard"
        elif style in {"conservative","c"}: BET_STYLE = "conservative"
        elif style in {"aggressive","a"}: BET_STYLE = "aggressive"
        else:
            print("betstyle must be: standard|conservative|aggressive")
            return
        print_rules(counter); return

    if cmd == "betmax" and len(parts) >= 2:
        try:
            n = int(parts[1])
            if n < 1 or n > 50: raise ValueError
            BET_MAX_UNITS = n
            print_rules(counter)
        except Exception:
            print("betmax must be an integer between 1 and 50.")
        return

    if cmd == "decks" and len(parts) >= 2:
        try:
            n = int(parts[1])
            counter.reset(n)
            print("Shoe reset.")
            print_rules(counter)
        except Exception as e:
            print("Usage: decks <1..8>")
        return

    if cmd == "shuffle":
        counter.reset(counter.num_decks)
        print("Shoe shuffled. Count reset.")
        print_rules(counter); return

    if cmd == "count":
        print(f"Running: {counter.running:+d}, True: {counter.true_count:+.2f}, Decks remaining: {counter.decks_remaining:.2f}")
        return

    if cmd == "seen":
        if len(parts) < 2:
            print("Usage: seen <cards>   e.g., seen 7,3,T,A,9")
            return
        try:
            batch = parse_hand(" ".join(parts[1:]))
            counter.add_seen(batch)
            print(f"Added seen: {','.join(batch)}")
            print(f"Running: {counter.running:+d}, True: {counter.true_count:+.2f}, Decks remaining: {counter.decks_remaining:.2f}")
        except Exception as e:
            print(f"Input error: {e}")
        return

    if cmd == "undo":
        if counter.undo():
            print("Undid last seen batch.")
            print(f"Running: {counter.running:+d}, True: {counter.true_count:+.2f}, Decks remaining: {counter.decks_remaining:.2f}")
        else:
            print("Nothing to undo.")
        return

    if cmd in {"help","rules"}:
        if cmd == "help": print(HELP)
        print_rules(counter)
        return

    if cmd in {"quit","exit"}:
        sys.exit(0)

    print("Unknown command. Type 'help' for options.")

def main():
    counter = CountTracker(DEFAULT_NUM_DECKS)
    print("Blackjack Trainer — Perfect Strategy + Hi-Lo Count + Bet Hints")
    print_rules(counter)
    print("Type 'help' for commands.\n")

    while True:
        try:
            hand_in = input("Your hand (e.g., A,7  or  8,8  or  T,6,3)  |  or command: ").strip()
            if not hand_in:
                continue
            # Commands
            parts = hand_in.split()
            if parts[0].lower() in {"set","decks","shuffle","count","seen","undo","help","rules","betstyle","betmax","quit","exit"}:
                set_option(parts, counter)
                continue
            if hand_in.lower() in {"q","quit","exit"}:
                break

            up_in = input("Dealer upcard (2-9, T/J/Q/K, A): ").strip()
            if up_in.lower() in {"q","quit","exit"}:
                break

            # Strategy advice
            cards = parse_hand(hand_in)
            up = parse_upcard(up_in)
            first_two = (len(cards) == 2)
            move = advise(cards, up, first_two=first_two)
            total, soft, _ = hand_total_and_soft(cards)
            kind = "Soft" if soft else "Hard"
            pair_note = " (Pair)" if first_two and is_pair(cards) else ""
            print(f"\n{kind} {total}{pair_note} vs {up} → {move}")

            # Counting input for this round
            seen_prompt = "Seen this round [Enter = count your hand + dealer upcard, or list all seen cards]: "
            seen_in = input(seen_prompt).strip()
            if not seen_in:
                batch = cards + [up]
            else:
                batch = parse_hand(seen_in)

            counter.add_seen(batch)
            tc = counter.true_count
            advice = bet_advice(tc, BET_STYLE, BET_MAX_UNITS)
            print(f"Running count: {counter.running:+d}   True count: {tc:+.2f}   Decks remaining: {counter.decks_remaining:.2f}")
            print(f"Bet suggestion: {advice}\n")

        except KeyboardInterrupt:
            print("\nExiting…")
            break
        except Exception as e:
            print(f"Input error: {e}\n")

if __name__ == "__main__":
    main()
