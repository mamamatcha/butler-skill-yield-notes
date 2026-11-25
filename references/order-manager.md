# A worked order: a better price than the book, given time

An ordinary open or buy takes the book now: a seller gets the bid, a buyer pays the ask.
The `options-order-manager@2` duty **works** the same trade instead: it asks Derive's
market makers, rests an order at Derive's own mark, and gives ground toward the book
step by step, never past the price the owner agreed. Most orders a maker will take fill
in the first minute; the rest wait, and may not fill at all.

**One of three ways on every Derive buy.** A buy quote with `worked` offers the order
book, RFQ and the order manager (`buying.md` § The shape, beat 5). The order manager goes
first, suggested, only when `worked.recommended` is true (§ The saving). The pick stays
theirs: "buy it now", "just buy it" files the ordinary buy. A put sale or a close
is worked only when they ask ("get me a better price", "work the order", "no rush").
**Derive only**: on Paradex and Rysk, say it works on Derive only.

## What is different

Beat 5's line says the first two before the yes; the third is said when it is filed.

1. **It trades from a wallet of its own.** The money leaves their main wallet on one
   funding card, and from then on the duty trades with no further approval, inside the
   ceiling they agreed. What it does not spend comes back to their main wallet on its
   own after the receipt, with no card; what it bought stays in that wallet's account.
2. **How it ends.** It starts at Derive's fair price and moves toward today's price. If
   nothing fills by the deadline, it takes the book, as long as the price is still
   inside their ceiling; past it, nothing is bought. Never say "if no one sells for
   less, nothing is bought": at the deadline it buys at the book's price.
3. **What it buys or sells stays in that account**, shown as its own Platforms row
   ("Derive · <the duty's title>"), not with their main Derive positions.

SKILL.md's "Never file without all four" holds unchanged: the bad case first, the plain
yes, and a quote run after their last answer.

## The saving

Say `worked.saves_up_to_usd` with `worked.saves_up_to_pct` of the premium: "up to $5.25
(1.1%)", never as a promise. It is two parts: the price, to a fill at Derive's mark
(`price_saves_usd`), and the fee, because a resting fill pays Derive's maker fee, not
the taker fee (`fee_saves_usd`). When the fee is most of it, say "mostly in fees". Never
offer `at_mark_saves_usd`: it leaves the fee out and says $0 on a book already at the mark.

The figure is live. A re-quote that changes it is said with why ("the price moved").

**When it is suggested.** `worked.recommended` is true on a buy of $1,000 or more whose
ask is 5% or more over Derive's mark: there waiting is worth the most. Then it goes
first, with the reason in one sentence from `worked.ask_over_fair_pct` ("the asking
price is 6.1% over Derive's fair price"). Otherwise it is listed third and never
suggested, and once they pick another way it is not brought up again.

## How long

`WORK_MINUTES` is theirs. None named: **60 for a buy**, 240 for a sale or a close; 15 for
"quick". There is no longest: it always ends an hour before expiry. "Until I cancel", "as
long as it takes": the minutes to expiry, and say that the longer a buy waits, the more
likely it misses the move they are betting on: the option gets dearer as the market
moves their way. Never promise no buy at the end: the deadline always tries the book
inside the ceiling.

## Filing it

1. Quote as SKILL.md step 2. A Derive quote carries `worked`:

   | Field | Means |
   | --- | --- |
   | `worked.params` | the duty's settings, passed as they are. `WORST_PRICE` is the bound per contract: the bid selling; buying, the ceiling an ordinary buy carries (`max_cost_usd`), with `FILL_NOW_PRICE` today's ask for the receipt |
   | `worked.fund_usdc` | what the duty's wallet starts with: the collateral, or the cost at the ceiling, plus the fee and 2% (at most $2) for the bridge, never under $12 |
   | `worked.saves_up_to_usd`, `worked.saves_up_to_pct` | the most working it could save, price and fee (§ The saving) |

   No `worked`: the quote is not Derive's, or has no live price; it cannot be worked.
2. Offer it as `buying.md` beat 5, or for a sale or close with step 3's sentences, then
   the three points above, the ceiling ("never over $35.20 for each ETH" buying, "never
   under $41" selling), how long, and `fund_usdc`. The yes to a buy is the yes to
   `max_cost_usd`. A lower ceiling of their own: set `WORST_PRICE` to `FILL_NOW_PRICE`
   (today's price), which stays inside it. Get a yes.
3. **Money left from an earlier one.** Before a new wallet, `duty_list`: each finished
   `options-order-manager` duty names its `walletId` (`@2` sends home all but under $3;
   `@1` sends nothing). `bevo-read get
   '/options/account?venue=derive&walletId=<LABEL>'` on each: free USDC there
   (`freeForNewPutsUsd`) is said once ("$486 is still in the wallet from your last
   order") with the offer to bring it home, never left unsaid.
4. A new wallet for it, then the duty:

   ```sh
   bevo-wallet create --chain ethereum --label <LABEL> --idempotency-key <KEY>:wallet
   ```

   ```json
   {"recipe": "options-order-manager@2", "movesFunds": true, "title": "Work {INSTRUMENT} for a better price",
    "walletId": "<LABEL>", "fundUsdc": <worked.fund_usdc>,
    "triggers": [{"kind": "timer", "intervalSeconds": 60}],
    "params": {<worked.params>, "WORK_MINUTES": <minutes>,
               "WITHDRAW_ON_FINISH": true, "WALLET_LABEL": "<LABEL>"}}
   ```

   One wallet per worked order, never one that holds money or serves another duty.
   Tell the owner to approve the funding card. No `acp options` command is filed from
   the chat. Make sure SKILL.md step 9's `options-lifecycle` duty exists: it watches
   what this wallet's account holds to expiry, as it does every other option.
5. The duty tells the owner when it starts, on each part fill, and at the end with a
   receipt: the average price, what that saved against the book in dollars and percent,
   and where each fill came from. Then it sends its free USDC home (Derive keeps about
   $1; under $3 stays), says how much went back, and finishes. Never poll it; `duty_show`
   and `duty_logs` when they ask how it is going.

**A change while it runs** ("give it longer", "keep going"): `duty_update` its params,
every other setting unchanged, then `duty_show`, and say only what the updated settings
do. A setting the recipe refuses is said as refused, never as done.

## Stopping it

**Never turn it off to stop it.** Turned off while an order rests, that order stays on
Derive and can still fill at its price until the option expires.

"Cancel it", "stop working it": `duty_update` its params with `"STOP": true` added,
every other setting unchanged. Within a minute it cancels what rests and sends the
receipt for what had filled. Found turned off with an order still resting: cancel it from
chat, `acp options cancel --order <id> --wallet <LABEL>`, a card (`--wallet` left out in
the duty's own chat).

## Afterwards

- **Look:** `bevo-read get '/options/account?venue=derive&walletId=<LABEL>'`.
- **Close what it holds:** quote the close (step 2); to work it, `duty_update` the same
  duty with that quote's `worked.params` (a new order; a close is worked by the makers
  and the book only). To close now: step 5's `acp options close … --wallet <LABEL>`, a card.
- **Bring the money home:** the duty does it after the receipt. For what it left (an `@1`
  duty, under $3, or a sold put's collateral once it settles): `account.md` § A duty's
  own wallet, out of Derive into this wallet, then into the main wallet, a card each.
  `duty_delete` is refused until then.
- At expiry Derive settles in cash into that same account; the lifecycle duty gives
  the heads-up and the outcome, naming this wallet.

## Say to the owner

Short paragraphs, one idea each, the question on its own line. Its line in a buy's
three ways (`buying.md` § Say to the owner has the whole offer):

"Order manager: it waits at Derive's fair price for up to an hour, up to $5.25 (1.1%)
saved, mostly in fees. If no one sells by then, it buys at the asking price, still under
your ceiling. It trades from a wallet of its own, funded by one $502 card; what it
doesn't spend comes back to you."

Filed: "It's set up. Approve the $502 funding card and it starts, with no more approvals
after that. What it buys is held in its own wallet's Derive account, and what it doesn't
spend comes back to your main wallet when it's done. You'll hear when it fills, or in
an hour with what it paid."

Stopped: "I've told it to stop. It takes its order off the book within a minute and
sends you what filled."
