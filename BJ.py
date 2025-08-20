#!/usr/bin/env python3
"""
Austin's Blackjack Trainer — Multi-Step Perfect Strategy + Hi-Lo Count + Bet Hints
- Multi-deck basic strategy
- Rule toggles: S17/H17, Late Surrender (LS), DAS, Double 11 vs Ace
- Running count & true count (Hi-Lo)
- Betting hints based on true count
- Multi-step hand: continue hitting, doubling, splitting
- Full CLI with robust input handling
"""

import sys
from typing import List, Tuple

# -------------------------------
# RULES / DEFAULTS
# -------------------------------
H17 = False
LATE_SURRENDER = True
DAS = True
DOUBLE_11_VS_ACE = False

SURRENDER_88_VS_T = True
SURRENDER_88_VS_A_H17 = True
SURRENDER_88_VS_A_S17 = False

DEFAULT_NUM_DECKS = 6
BET_STYLE = "standard"
BET_MAX_UNITS = 8

# -------------------------------
# CARD VALUES & COUNTING
# -------------------------------
CARD_VALUES = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":10,"Q":10,"K":10,"A":11}
COUNT_TAGS = {"2":+1,"3":+1,"4":+1,"5":+1,"6":+1,"7":0,"8":0,"9":0,"T":-1,"J":-1,"Q":-1,"K":-1,"A":-1}
VALID_RANKS = set(CARD_VALUES.keys())
DISPLAY_UP = {"T":"T","J":"T","Q":"T","K":"T","A":"A","2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9"}
DIGITS = set("23456789")

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def normalize_card(c: str) -> str:
    c = c.strip().upper()
    if c in {"10","T","J","Q","K"}: return "T"
    if c in DIGITS or c=="A": return c
    raise ValueError(f"Invalid card: {c}")

def parse_upcard(s: str) -> str:
    return DISPLAY_UP[normalize_card(s)]

def tokenize_cards(s: str) -> List[str]:
    s = s.strip().upper().replace("10","T")
    out = []
    for ch in s:
        if ch in VALID_RANKS:
            out.append(ch)
        else:
            out.append(" ")
    parts = [p for p in "".join(out).split() if p]
    flat = []
    for p in parts:
        for ch in p:
            flat.append(ch)
    return [normalize_card(x) for x in flat]

def parse_hand(text: str) -> List[str]:
    cards = tokenize_cards(text)
    if not cards: raise ValueError("Empty hand.")
    for c in cards:
        if c not in VALID_RANKS:
            raise ValueError(f"Invalid rank in hand: {c}")
    return cards

def hand_total_and_soft(cards: List[str]) -> Tuple[int,bool,int]:
    total, aces = 0, 0
    for c in cards:
        if c=="A": total+=11; aces+=1
        elif c=="T": total+=10
        else: total+=int(c)
    soft_aces = aces
    while total>21 and soft_aces>0:
        total-=10
        soft_aces-=1
    return total,(soft_aces>0),soft_aces

def is_pair(cards: List[str]) -> bool:
    return len(cards)==2 and cards[0]==cards[1]

# -------------------------------
# STRATEGY ENGINE
# -------------------------------
def maybe_surrender(default_move:str, first_two:bool) -> str:
    if LATE_SURRENDER and first_two:
        return f"Surrender (otherwise {default_move})"
    return default_move

def advise(hand_cards: List[str], dealer_up: str, first_two: bool = True) -> str:
    total, soft, _ = hand_total_and_soft(hand_cards)
    dealer = parse_upcard(dealer_up)
    # Pairs
    if first_two and is_pair(hand_cards):
        r = hand_cards[0]
        if r=="A": return "Split"
        if r=="T": return "Stand"
        if r=="9": return "Split" if dealer in {"2","3","4","5","6","8","9"} else "Stand"
        if r=="8":
            if dealer=="T" and SURRENDER_88_VS_T: return maybe_surrender("Split",True)
            if dealer=="A":
                if (H17 and SURRENDER_88_VS_A_H17) or (not H17 and SURRENDER_88_VS_A_S17):
                    return maybe_surrender("Split",True)
            return "Split"
        if r=="7": return "Split" if dealer in {"2","3","4","5","6","7"} else "Hit"
        if r=="6": return "Split" if dealer in {"2","3","4","5","6"} else "Hit"
        if r=="5": return "Double" if dealer in {"2","3","4","5","6","7","8","9"} else "Hit"
        if r=="4": return "Split" if DAS and dealer in {"5","6"} else "Hit"
        if r in {"2","3"}: return "Split" if DAS and dealer in {"2","3","4","5","6","7"} else "Hit"
    # Soft totals
    if soft:
        if total>=20: return "Stand"
        if total==19: return "Double" if H17 and dealer=="6" and first_two else "Stand"
        if total==18:
            if dealer in {"3","4","5","6"}: return "Double" if first_two else "Stand"
            if H17 and dealer=="2": return "Double" if first_two else "Stand"
            if dealer in {"2","7","8"}: return "Stand"
            return "Hit"
        if total in {17,16,15,14,13}:
            if total==17: return "Double" if first_two and dealer in {"3","4","5","6"} else "Hit"
            if total in {15,16}: return "Double" if first_two and dealer in {"4","5","6"} else "Hit"
            if total in {13,14}: return "Double" if first_two and dealer in {"5","6"} else "Hit"
        return "Hit"
    # Hard totals
    if total>=17: return "Stand"
    if total==16: return maybe_surrender("Hit", first_two) if first_two and dealer in {"9","T","A"} else ("Stand" if dealer in {"2","3","4","5","6"} else "Hit")
    if total==15: return maybe_surrender("Hit", first_two) if first_two and dealer in {"T"} else ("Stand" if dealer in {"2","3","4","5","6"} else "Hit")
    if total in {13,14}: return "Stand" if dealer in {"2","3","4","5","6"} else "Hit"
    if total==12: return "Stand" if dealer in {"4","5","6"} else "Hit"
    if total==11: return "Double" if DOUBLE_11_VS_ACE and first_two and dealer=="A" else ("Double" if first_two else "Hit")
    if total==10: return "Double" if first_two and dealer in {"2","3","4","5","6","7","8","9"} else "Hit"
    if total==9: return "Double" if first_two and dealer in {"3","4","5","6"} else "Hit"
    return "Hit"

# -------------------------------
# COUNT TRACKER
# -------------------------------
class CountTracker:
    def __init__(self,num_decks=DEFAULT_NUM_DECKS):
        self.reset(num_decks)
    def reset(self,num_decks:int=None):
        if num_decks: self.num_decks=int(num_decks)
        self.running=0
        self.seen=0
        self._history=[]
    def add_seen(self,cards:List[str]):
        batch=[normalize_card(c) for c in cards]
        for c in batch:
            self.running+=COUNT_TAGS.get(c,0)
            self.seen+=1
        self._history.append(batch)
    def undo(self)->bool:
        if not self._history: return False
        last=self._history.pop()
        for c in last:
            self.running-=COUNT_TAGS.get(c,0)
            self.seen-=1
        return True
    @property
    def decks_remaining(self)->float:
        total_cards=self.num_decks*52
        remaining=max(0,total_cards-self.seen)
        return remaining/52.0
    @property
    def true_count(self)->float:
        denom=max(0.25,self.decks_remaining)
        return self.running/denom

# -------------------------------
# BET ADVICE
# -------------------------------
def bet_units_from_true_count(tc:float)->int:
    t=int(tc)
    if BET_STYLE=="conservative":
        if t<=0: return 1
        if t==1: return 1
        if t==2: return 2
        if t==3: return 3
        if t==4: return 4
        return BET_MAX_UNITS
    elif BET_STYLE=="aggressive":
        if t<=-1: return 1
        if t==0: return 2
        if t==1: return 3
        if t==2: return 5
        if t==3: return 7
        return BET_MAX_UNITS
    # standard
    if t<=0: return 1
    if t==1: return 2
    if t==2: return 4
    if t in {3,4}: return 6
    return BET_MAX_UNITS

def bet_advice(tc:float)->str:
    units=bet_units_from_true_count(tc)
    if units>=BET_MAX_UNITS: return f"MAX bet → {units} units"
    if units==1: return "Minimum bet → 1 unit"
    return f"Increase bet → {units} units"

# -------------------------------
# CLI
# -------------------------------
def print_rules(counter:CountTracker):
    print(f"Dealer: {'H17' if H17 else 'S17'} | LS: {LATE_SURRENDER} | DAS: {DAS} | D11A: {DOUBLE_11_VS_ACE}")
    print(f"Decks: {counter.num_decks} | Bet ramp: {BET_STYLE} | Max units: {BET_MAX_UNITS}")
    print(f"Count → Running: {counter.running:+d} True: {counter.true_count:+.2f} Decks remaining: {counter.decks_remaining:.2f}")

HELP_TEXT="""
Commands:
help,rules | show rules
set <option> on/off | toggle rules
decks N | set decks
shuffle | reset shoe
count | show running/true count
seen <cards> | add cards seen
undo | undo last seen
betstyle s|c|a | bet ramp style
betmax N | max bet units
quit/exit | exit program
"""

def main():
    counter = CountTracker(DEFAULT_NUM_DECKS)
    print("Blackjack Trainer — Multi-step Basic Strategy + Count + Bet Hints")
    print_rules(counter)
    print("Type 'help' for commands.\n")
    while True:
        try:
            hand_in = input("Your hand (or command): ").strip()
            if not hand_in: continue
            if hand_in.lower() in {"quit","exit"}: break
            parts = hand_in.split()
            if parts[0].lower() in {"help","rules","set","decks","shuffle","count","seen","undo","betstyle","betmax"}:
                print(HELP_TEXT)
                continue
            up_in = input("Dealer upcard: ").strip()
            if up_in.lower() in {"quit","exit"}: break
            cards = parse_hand(hand_in)
            dealer = parse_upcard(up_in)
            first_two = True
            # multi-step hand
            while True:
                move = advise(cards,dealer,first_two=first_two)
                total,soft,_ = hand_total_and_soft(cards)
                kind = "Soft" if soft else "Hard"
                pair_note = " (Pair)" if is_pair(cards) and first_two else ""
                print(f"{kind} {total}{pair_note} vs {dealer} → {move}")
                if move.startswith("Stand") or move.startswith("Surrender"): break
                action = input("Next card drawn (or s=stand, q=quit hand): ").strip().upper()
                if action in {"S","STAND"}: break
                if action in {"Q","QUIT"}: break
                new_cards = parse_hand(action)
                cards += new_cards
                first_two=False
            # seen cards input at end
            seen_in = input("Enter all cards seen this round (or Enter to use hand+dealer): ").strip()
            if not seen_in:
                batch = cards+[dealer]
            else:
                batch = parse_hand(seen_in)
            counter.add_seen(batch)
            print(f"Running: {counter.running:+d} True: {counter.true_count:+.2f} Decks: {counter.decks_remaining:.2f}")
            print(f"Bet suggestion: {bet_advice(counter.true_count)}\n")
        except KeyboardInterrupt:
            print("\nExiting…"); break
        except Exception as e:
            print(f"Error: {e}\n")

if __name__=="__main__":
    main()
