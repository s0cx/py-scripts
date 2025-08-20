#!/usr/bin/env python3
# Austin's Blackjack Basic Strategy Advisor (Multi-deck)
# - Covers pairs, soft totals, hard totals
# - Rule toggles: S17/H17, Late Surrender (LS), Double After Split (DAS),
#                 Double 11 vs Ace (rare rule/table-dependent)
# - Two-card restrictions respected (Double/Surrender/Split only on first decision)
# - Robust input parsing: "A,7", "A-7", "A7", "AT", "T,6,3", "8 8", etc.

from typing import List, Tuple

# ---------- DEFAULT TABLE RULES ----------
H17 = False                # True: dealer hits soft 17; False: stands on soft 17 (S17)
LATE_SURRENDER = True      # LS available on first decision only
DAS = True                 # Double after split
DOUBLE_11_VS_ACE = False   # Some charts allow double 11 vs A; default False for multi-deck
# Edge case toggles (leave defaults unless you know your table):
SURRENDER_88_VS_T = True   # 8,8 vs T -> Surrender (otherwise Split)
SURRENDER_88_VS_A_H17 = True   # 8,8 vs A: surrender on H17 (otherwise Split)
SURRENDER_88_VS_A_S17 = False  # 8,8 vs A: surrender on S17 (otherwise Split)

# ----------------------------------------

DIGITS = set("23456789")
VALID_SINGLE = set(list(DIGITS) + ["T","J","Q","K","A"])
DISPLAY_RANK = {"T": "T", "J":"T", "Q":"T", "K":"T", "A":"A",
                "2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9"}

def normalize_card(c: str) -> str:
    c = c.strip().upper()
    if c in {"10","T","J","Q","K"}:
        return "T"
    if c in DIGITS or c == "A":
        return c
    raise ValueError(f"Invalid card: {c}")

def tokenize_cards(s: str) -> List[str]:
    """Accepts inputs like 'A,7', 'A-7', 'A7', 'AT', 'T,6,3', '8 8'."""
    s = s.strip().upper()
    s = s.replace("10", "T")
    # If separators exist, split on them
    for sep in [",", " ", "-", "/", "|", ";", ":"]:
        if sep in s:
            parts = [p for p in s.replace(sep, " ").split() if p]
            return [normalize_card(p) if len(p) == 1 else
                    [normalize_card(x) for x in p] if len(p) > 1 else p
                    for p in parts]  # we might still have "AT" segments
    # No obvious separators — parse char by char
    parts = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in {"A","K","Q","J","T"} or ch in DIGITS:
            parts.append(ch)
            i += 1
        else:
            raise ValueError(f"Invalid character in hand: '{ch}'")
    # Flatten in case a segment was multi-char like "AT" captured above
    flat = []
    for p in parts:
        if isinstance(p, list):
            flat.extend(p)
        else:
            flat.append(p)
    return [normalize_card(x) for x in flat]

def parse_hand(text: str) -> List[str]:
    tokens = tokenize_cards(text)
    # Some paths above may produce nested lists; ensure flat + normalized
    out = []
    for t in tokens:
        if isinstance(t, list):
            out.extend(t)
        else:
            out.append(t)
    return [normalize_card(x) for x in out]

def parse_upcard(s: str) -> str:
    s = s.strip().upper().replace("10","T")
    c = normalize_card(s)
    # Collapse faces to T for strategy purposes
    return "A" if c == "A" else ("T" if c == "T" else c)

def hand_total_and_soft(cards: List[str]) -> Tuple[int, bool, int]:
    """Return (total, soft_flag, soft_aces_remaining_as_11)."""
    total = 0
    aces = 0
    for c in cards:
        if c == "A":
            total += 11
            aces += 1
        elif c == "T":
            total += 10
        else:
            total += int(c)
    # Reduce Aces from 11->1 as needed
    soft_aces = aces
    while total > 21 and soft_aces > 0:
        total -= 10
        soft_aces -= 1
    soft = (soft_aces > 0)
    return total, soft, soft_aces

def is_pair(cards: List[str]) -> bool:
    return len(cards) == 2 and cards[0] == cards[1]

def maybe_surrender(default_move: str, first_two: bool) -> str:
    if LATE_SURRENDER and first_two:
        return f"Surrender (otherwise {default_move})"
    return default_move

def advise(hand_cards: List[str], dealer_up: str, first_two: bool = True) -> str:
    """
    Core strategy engine. Returns one of:
      - 'Hit', 'Stand', 'Double', 'Split', or 'Surrender (otherwise X)'
    """
    total, soft, _ = hand_total_and_soft(hand_cards)
    dealer = parse_upcard(dealer_up)

    # -------- Pair decisions (two-card only) --------
    if first_two and is_pair(hand_cards):
        r = hand_cards[0]  # already normalized
        if r == "A":
            return "Split"
        if r == "T":
            return "Stand"
        if r == "9":
            # Split vs 2-6,8,9; Stand vs 7,10,A
            return "Split" if dealer in {"2","3","4","5","6","8","9"} else "Stand"
        if r == "8":
            # 8,8 is special: LS vs T (and often vs A on H17), else Split
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
            # Treat as hard 10
            return "Double" if dealer in {"2","3","4","5","6","7","8","9"} else "Hit"
        if r == "4":
            # Split only vs 5-6 when DAS; otherwise Hit
            if DAS and dealer in {"5","6"}:
                return "Split"
            return "Hit"
        if r in {"2","3"}:
            # With DAS: split vs 2-7. Without DAS: split vs 4-7.
            if DAS and dealer in {"2","3","4","5","6","7"}:
                return "Split"
            if not DAS and dealer in {"4","5","6","7"}:
                return "Split"
            return "Hit"

    # -------- Soft totals --------
    if soft:
        # 20 or 21: always Stand
        if total >= 20:
            return "Stand"

        # A,8 (19)
        if total == 19:
            # H17: Double vs 6, else Stand. S17: Stand.
            if H17 and dealer == "6":
                return "Double" if first_two else "Stand"
            return "Stand"

        # A,7 (18)
        if total == 18:
            if dealer in {"3","4","5","6"}:
                return "Double" if first_two else "Stand"
            if H17 and dealer == "2":
                return "Double" if first_two else "Stand"
            if dealer in {"2","7","8"}:
                return "Stand"
            # vs 9,T,A -> Hit
            return "Hit"

        # A,6 (17)
        if total == 17:
            return "Double" if first_two and dealer in {"3","4","5","6"} else "Hit"

        # A,4 / A,5 (15/16)
        if total in {15, 16}:
            return "Double" if first_two and dealer in {"4","5","6"} else "Hit"

        # A,2 / A,3 (13/14)
        if total in {13, 14}:
            return "Double" if first_two and dealer in {"5","6"} else "Hit"

        return "Hit"

    # -------- Hard totals --------
    if total >= 17:
        return "Stand"

    if total == 16:
        # LS: 16 vs 9/T/A
        if dealer in {"9","T","A"} and first_two:
            return maybe_surrender("Hit", first_two=True)
        return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"

    if total == 15:
        # LS: 15 vs T (and on H17 often vs 9)
        if first_two:
            if dealer == "T":
                return maybe_surrender("Hit", first_two=True)
            if H17 and dealer == "9":
                return maybe_surrender("Hit", first_two=True)
        return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"

    if total in {13, 14}:
        return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"

    if total == 12:
        return "Stand" if dealer in {"4","5","6"} else "Hit"

    if total == 11:
        if dealer == "A":
            return "Double" if (DOUBLE_11_VS_ACE and first_two) else "Hit"
        return "Double" if first_two else "Hit"

    if total == 10:
        return "Double" if first_two and dealer in {"2","3","4","5","6","7","8","9"} else "Hit"

    if t
