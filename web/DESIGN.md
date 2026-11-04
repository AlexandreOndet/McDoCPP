# McDoCPP web: design notes

Subject: a points wallet that tells you which McDonald's food to cash in for, at this counter, today. Audience: Canadians who already have the app open. Primary job: answer "what do I redeem?" without scrolling.

## Tokens
Color (dark, default): bg #1B1310, surface #271C16, surface-2 #33261E, border #40312A, text #FFF3E3, muted #C9B5A3, gold #F6C443, gold-hi #FFD970, ink-on-gold #1B1310 / #4A2E1E, success #9FE0B0, warn #F2A58D.
Light (prefers-color-scheme): bg #FFF7EA, surface #FFFFFF, surface-2 #F6E9D6, border #E4D3BE, text #1B1310, muted #6B5A4D, gold #D99A00 (text) / #F6C443 (fills), success #2F7D4A, warn #B8471F.
Type: Bricolage Grotesque (variable, 800 display with opsz) for numerals, tier labels, item names on the hero; Nunito Sans 400/600/700 for everything else. Scale: 13 / 15 / 17 / 22 / 28 / 38 / 56 / 96.
Radius: 24 cards and hero, 20 item cards, 999 pills. Dividers: 1px dashed border, receipt-like.

## Layout
Desktop
```
[¢ McDoCPP]  What are your points worth at this McDonald's?        [store ▾] [FR]
┌─ wallet 5/12 ───────────────┐ ┌─ best pick (gold) 7/12 ─────────────────────┐
│ 6,000 pts  (big input)      │ │ (food illustration)  Best thing to get now   │
│ ▓▓▓▓▓▓▓▓░░░░ 2k 4k 6k 10k  │ │                       6 pc McNuggets          │
│ 4,000 pts to the next shelf │ │                       12.32¢ per 100 pts      │
│ ☐ skip breakfast-only       │ │                       $1.23 / 1,000 pts        │
└─────────────────────────────┘ │  Or wait 4,000 pts: nuggets 10 pays 10.69¢   │
                                └───────────────────────────────────────────────┘
 2k │ 4 rewards, best 12.95¢           ┆ card ┆ card ┆ card ┆ card ┆  (snap row)
────┼ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
 4k │ ...
10k │ 4,000 pts to unlock   (dimmed, still readable)
[ map + search: "Same points, different store" ]
```
The tier numeral sits in a left rail at display size and is the only label the shelf needs. Content is left aligned; numerals in cards are right aligned on the same baseline so a column of CPPs reads like a bill.

Phone: wallet input sticky at top (compact, one line, meter below), hero card, shelves as horizontal snap rows with the tier numeral as the row's first "card", map as a bottom sheet behind a "Map" button.

## Principles
- The hero numeral is the one bold thing. Everything else is quiet surfaces and dashed rules.
- Illustrations carry identity; no icons for food, no emoji.
- Copy is conversational and sentence case: "4,000 pts to unlock", not "LOCKED".
- Money formatting everywhere; CPP shown ×100 as ¢ per 100 pts (= per $1 spent) with $/1,000 pts beside it.

## Review against defaults (what changed)
- Dropped the mockup's tracked ALL-CAPS eyebrows ("POINTS IN YOUR WALLET") for sentence-case labels; caps eyebrows are template chrome.
- No middle-dot meta strings; shelf notes are sentences.
- Shelf rail numeral instead of an h2 + note row, so the page reads as a menu board rather than a card grid with headings.
- Hero on gold is kept from the approved mockup (brief), but the decorative circle is replaced by the illustration bleeding off the card edge.
- Locked state uses opacity and a plain sentence; no padlock icon.
