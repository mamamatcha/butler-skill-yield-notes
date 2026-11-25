# Buying a call or a put

Buying an option is **not yield**. The owner pays a price up front - the premium plus
Derive's fee - and gets the right to a payout at expiry:

- a **call** pays (settlement price - strike) x size if the asset ends **above** the
  strike: upside on a rise, without buying the asset;
- a **put** pays (strike - settlement price) x size if it ends **below** the strike: a
  bet on a fall, or a hedge for an asset they already hold.

If the asset does not end past the strike, the option expires worthless and the whole
cost is gone. That cost is also the most they can lose: nothing is borrowed and
nothing is locked beyond it.

## The first-time check

Before an owner's first bought option ever, get three plain yes answers. If any is no
or vague, do not quote:

- "You can lose everything you pay for this. Clear?"
- "It only makes money if ETH ends past the breakeven on the expiry date, and it is
  worth a little less every day ETH stands still. Clear?"
- "You can sell it back before then, but only for what the market pays at the time,
  often less than you paid. Clear?"

And before every buy, an explicit yes to the number: "You can lose the whole
$199.54 - yes?" A yes to the idea is not a yes to the amount. The figure goes in the
question itself, card or text; "the entire amount spent is gone" is not a number.

## Choosing is theirs

Butler never picks the trade. "Just buy whatever looks good", "you pick", "the best
one": say Butler does not choose trades, and ask which asset, the most they will
spend, and roughly when it should expire. Quote nothing until they have named an
asset and an amount. Never make up a budget, even a small one. Monthly by default:
weeklies lose too much to fees and the spread. Asked for ideas once they have named
those, give the choices first; "the pick is yours" comes after them, never as the
opening sentence.

The helper's strike rule is a starting point, said as one in the headline, with the
quote's own numbers: "(5% above today's price)". `--delta 0.3` instead of `--otm-pct` holds the odds steady
if they ask for that. A strike they named ("the 2100 put") is `--strike 2100`, with
`--expiry` for the day (`YYYY-MM-DD`): never a rule that lands near it, and never a
price read off `chain`. A quote whose `strike` or `expiry` is not what they named is not
offered; an expiry without that strike is refused with the strikes it lists, so say
those and ask.

## Saying it out loud

Every number is a **field on the buy quote**. Never compute one.

| In the sentence | Field |
| --- | --- |
| what it costs today, and the most they pay | `total_cost_usd` and `max_cost_usd`, in the cost bullet (§ The shape). The premium and fee add up to `total_cost_usd`, never to the ceiling: never put them after "at most" |
| the most they can lose | the ceiling: `max_cost_usd` (the card's "You pay at most"), or the one they set (below) |
| fees | `fee_usd`, always its own bullet, split when `platform_fee_usd` is above 0: "Fees: $0.65 ($0.62 Derive, $0.03 Virtuals platform fee), included". At 0: "Fees: $0.62, all Derive's; no Virtuals platform fee". Always the words "Virtuals platform fee", never "platform" alone, and never Butler's. The receipt after the fill says it the same way, at 0 too |
| where it starts paying at expiry | `breakeven` |
| the price it turns on | `strike` |
| the date | `expiry`, its time as given, never one from memory |
| how much | `size`, in units of the asset |
| how good the price is | `overpay_vs_fair_vol_pts` |
| a wide book, or one that holds less than the size | each of `warnings`, a bullet each, then `rfq_offer` when the quote has it, before the closing question. On Derive, RFQ is already one of the three ways: the warning, never `rfq_offer` |

## The shape

Short bullets, one fact each, a few words; never a paragraph. The question on its own
line. In this order:

1. **Headline**: size, option, strike (the strike rule, as one), expiry.
2. **Cost**: `total_cost_usd` now and `max_cost_usd`, with its room said once.
3. **Fees**: `fee_usd`, split (§ Saying it out loud).
4. **Pays**: what it pays per dollar past the strike, and `breakeven`.
5. **Settles**: `expiry`'s day and time; they can sell it back before then.
6. Each of `warnings`, a bullet each.
7. **On Derive (a quote with `worked`), three ways, numbered:**
   - **Order book**: market (now, at the ask) or limit (a price they name: `resting.md`).
   - **RFQ**: the makers quote; on Derive it fills only if a quote beats the book and
     their limit (`rfq.md`). At `min_size`, add that makers may not quote one so small.
   - **Order manager**: it rests at Derive's fair price for up to an hour and reprices
     as the market moves; `worked.saves_up_to_usd` (`saves_up_to_pct`) as an estimate;
     unfilled by then, it buys at the ask, never over the ceiling (`order-manager.md`).

   In that order, unless `worked.recommended` is true: then the order manager first,
   marked recommended with its reason in a few words (the ask is
   `worked.ask_over_fair_pct` above Derive's fair price). Never mark it otherwise.
8. **The question**: the route and the yes to the number, one line: "Which route? You
   can lose up to $499.56 - OK?" A yes with no route takes the first one listed; say
   which as it is filed. Off Derive, the yes alone.

"Not yield" is said only when they came asking for yield or income. A put's pays
bullet reads "below": "Pays $3.45 for every $1 ETH is below $2,350 on 30 Oct; profit
below ~$2,295."

## The ceiling

`max_cost_usd` is `total_cost_usd` plus room, so a small move between the quote and
the fill does not stop it. The order fills at the best ask up to the ceiling; if the
price holds, they pay about `total_cost_usd`. The cost bullet says the room and that
they can set their own, once; do not ask about it. A yes to the
amount is a yes to `max_cost_usd`.

If they name their own ceiling ("no more than $195", "no room"), it replaces
`max_cost_usd` everywhere: in the yes, in funding, and in `--max-cost`. Naming it is
not the yes: ask again with it, "You can lose the whole $195 - yes?", and file only
after that yes. Never pick a different ceiling for them.

- Under `total_cost_usd`: it would not fill at today's price. Say that and ask again.
- With a budget, never over `budget_usd`; for more, quote again with the new budget.
- Less room means more no-fills. A buy that does not fill moved past their ceiling:
  re-quote and re-ask, never re-file the same ceiling.
- Worked by the order manager, the buy carries the same ceiling (`worked.params`): it
  starts at Derive's fair price and may pay up to it, never more.

## Words

| Do not say | Say |
| --- | --- |
| "invest", "yield", "earn" | "pay $190 for the chance of a payout" |
| "protected", "insured", "safe" | "if ETH ends below $2,350, the put pays the difference in USDC" |
| "you can't lose more than…" as comfort | "you can lose all $199.54" |
| "it will pay if ETH goes up" | "it pays if ETH is above $2,664 on 30 October" |
| "cheap" | the price, and `overpay_vs_fair_vol_pts` if it is wide |

## When the price is poor

The ask over Derive's own mark is what the buyer gives away crossing the spread.

- over 10% of the option's value: a `warning`. Say it as written; the choice is theirs.
- over 20%: the `spread` safeguard holds the buy back until they waive it
  (`references/helper.md` § Safeguards).

Either one, or a best ask that holds less than the size, puts `rfq_offer` on the quote:
end the offer with it, as written (`references/helper.md`). On Derive, the three ways
already offer RFQ: say the warning, not `rfq_offer`.

## A hedge

A put on an asset they hold limits the loss on it below the strike, for a price.
Quote it with `--size` set to what they hold (never more - beyond that it is a bet on
a fall, not a hedge). Say what it does not do: it pays USDC into the Derive account at
expiry; it does not sell their ETH, and between the strike and spot they still carry
the fall.

## Closing early

An option the owner **bought** shows in `acp options account` positions with a
positive `size`; a sold note shows negative, and closing that one is a buy-back
(`references/selling.md`).

**The size is theirs, up to what they hold.** Read `positions` first. Asked to close
more than the position ("sell 5 of my ETH calls" with 0.16 held), say so and ask:
"You hold 0.16 of that call, not 5. Sell all 0.16?" Never shrink the size quietly,
and never pick between two positions for them.

Quote the close with `quote --side close --instrument <name> --size <size>`. Say
`net_proceeds_usd` against what they paid (the position's `costUsd`), plainly
when it is less: "Selling back now gets about $178.73 after fees, against $190.03 you
paid." Give any `warnings` as written ("fees take 16% of what the bid pays").

**Then ask for the floor**, the least they will take, with `min_proceeds_usd` as the
suggestion: "The least you'd take? I'd suggest $169.79, so a small move doesn't stop
it." File only the floor they agreed, and quote again after their answer: the card
needs a quote under 60 seconds old.

If it does not fill, nobody bought at that floor; the price moved. Say exactly that,
never "no liquidity", and re-quote before offering again, never re-filing the same
floor. On Derive or Paradex, offer RFQ with that re-quote (`references/rfq.md`). With `no live bid`, nobody is bidding for this option right now: holding it to
expiry costs nothing, and the lifecycle duty reports the outcome.

A close sells only what they hold (`reduce_only` on the venue). Nothing is filed or
deleted after it: the lifecycle duty watches whatever the account still holds.

## At expiry

Derive settles in cash at the `expiry` time. A bought option that ends in
the money pays automatically into the Derive account: (settle - strike) x size for a
call, (strike - settle) x size for a put. Nothing has to be done to collect it. It
stays in the account until withdrawn. One that ends out of the money pays nothing.

The lifecycle duty (SKILL.md step 9) tells the owner the day before and again with the
outcome, for every option the account holds. Nothing is filed for it per buy.

A bought option pays cash and buys nothing, so it is never `options-put-delivery`.

## Say to the owner

On Derive (a $500 ETH call):

```text
5.48 ETH calls at $1,750 (5% above today's price), expiring 25 Dec:

- Cost: ~$475.77 now; at most $499.56 if the price moves (you can set your own).
- Fees: $5.59 ($3.24 Derive, $2.35 Virtuals platform fee), included.
- Pays $5.48 for every $1 ETH is above $1,750 on 25 Dec; profit above ~$1,837.
- Settles 25 Dec, 08:00 UTC; you can sell it back before then.

Three ways to buy it on Derive:

1. Order book: market (now, at the ask) or limit (your price).
2. RFQ: I ask the market makers; it fills only if a quote beats the book and your limit.
3. Order manager: I rest orders at Derive's fair price for up to 1 hour and reprice as
   ETH moves. Est. $16.02 (3.4%) saved. Unfilled by then, it buys at the ask, never
   over $499.56.

Which route? You can lose up to $499.56 - OK?
```

With `worked.recommended` and a warning (a $2,500 ETH call, the ask 6% above fair):

```text
119.04 ETH calls at $2,050 (23% above today's price), expiring 25 Dec:

- Cost: ~$2,380.83 now; at most $2,499.88 if the price moves (you can set your own).
- Fees: $71.45 ($59.90 Derive, $11.55 Virtuals platform fee), included.
- Pays $119.04 for every $1 ETH is above $2,050 on 25 Dec; profit above ~$2,070.
- Settles 25 Dec, 08:00 UTC; you can sell it back before then.
- Only 81.18 contracts at the best ask: buying now may fill part-way.

Three ways to buy it on Derive:

1. Order manager (recommended: the ask is 6% above Derive's fair price): I rest
   orders at fair price for up to 1 hour and reprice as ETH moves. Est. $135.33 (5.9%)
   saved. Unfilled by then, it buys at the ask, never over $2,499.88.
2. Order book: market (now, at the ask) or limit (your price).
3. RFQ: I ask the market makers; it fills only if a quote beats the book and your limit.

Which route? You can lose up to $2,499.88 - OK?
```

On Paradex, a warning and `rfq_offer`:

```text
- …
- Only 25 contracts at the best ask: buying now may fill part-way.

Order book or RFQ (the makers get 20 seconds to quote inside your limit)?
You can lose up to $2,034.90 - OK?
```
