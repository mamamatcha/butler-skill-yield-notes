"""`scripts/quote.py`: the Virtuals platform fee in every Derive quote, read from the account, offline."""
import contextlib
import io
import json
import pathlib
import subprocess
import sys
import types
import unittest
from unittest import mock

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "quote.py"

ETH_CALL = "ETH-20261204-1900-C"
INST = {
    "instrument_name": ETH_CALL, "is_active": True,
    "option_details": {"strike": "1900", "expiry": 4_000_000_000, "option_type": "C"},
    "amount_step": "0.01", "minimum_amount": "0.01",
    "base_fee": "0.5", "taker_fee_rate": "0.0003", "mark_price_fee_rate_cap": "0.125",
}
TICKER = {"b": "48", "B": "10", "a": "50", "A": "10", "M": "49", "I": "2000",
          "option_pricing": {"bi": "0.60", "ai": "0.62", "i": "0.61", "d": "0.5"}}


def account(body=None, code=0, stderr="", raises=None):
    """A stand-in for `acp options account --venue derive --json`, recording each call."""
    calls = []

    def run(argv, **kw):
        calls.append(argv)
        if raises:
            raise raises
        out = body if isinstance(body, str) else json.dumps(body or {})
        return subprocess.CompletedProcess(argv, code, stdout=out, stderr=stderr)
    return types.SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired), calls


def helper(acp):
    mod = types.ModuleType("quote")
    exec(compile(SCRIPT.read_text(), str(SCRIPT), "exec"), mod.__dict__)
    mod.active_options = lambda cur, t: [INST]
    mod.tickers_for = lambda cur, expiry: {ETH_CALL: TICKER}
    mod.time = types.SimpleNamespace(time=lambda: 3_990_000_000)
    mod.subprocess = acp
    return mod


def run(h, *argv):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(sys, "argv", ["quote.py", *argv]), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            h.main()
            code = 0
        except SystemExit as exc:
            code = exc.code
        except Exception as exc:  # noqa: BLE001 - as __main__ reports it
            err.write("error: %s\n" % exc)
            code = 1
    return code, out.getvalue(), err.getvalue()


CLOSE = ("quote", "--side", "close", "--instrument", ETH_CALL, "--size", "1")


class PlatformFeeTest(unittest.TestCase):
    def quote(self, rate_body, *argv):
        acp, calls = account(rate_body)
        code, out, err = run(helper(acp), "quote", *argv)
        self.assertEqual(code, 0, err)
        return json.loads(out), calls

    def test_the_rate_comes_from_the_derive_account(self):
        q, calls = self.quote({"platformFeeRate": 0.005}, *CLOSE[1:])
        self.assertEqual(calls, [["acp", "options", "account", "--venue", "derive", "--json"]])
        self.assertEqual((q["fee_usd"], q["venue_fee_usd"], q["platform_fee_usd"]), (1.34, 1.1, 0.24))
        self.assertEqual(q["net_proceeds_usd"], 46.66)  # 48 - 1.10 - 0.24

    def test_zero_is_derives_fee_alone(self):
        q, _ = self.quote({"platformFeeRate": 0}, *CLOSE[1:])
        # 0.5 + min(0.0003 x 2000, 0.125 x 49) = 1.10
        self.assertEqual((q["fee_usd"], q["venue_fee_usd"], q["platform_fee_usd"]), (1.1, 1.1, 0))
        self.assertEqual(q["net_proceeds_usd"], 46.9)

    def test_a_server_too_old_to_report_it_charges_half_a_percent(self):
        q, _ = self.quote({"account": {"exists": True}}, *CLOSE[1:])
        self.assertEqual(q["platform_fee_usd"], 0.24)

    def test_an_unreadable_account_stops_the_quote(self):
        for acp in (account(code=4, stderr="[options] could not read the derive account (503)")[0],
                    account(raises=FileNotFoundError("acp"))[0],
                    account(body="<html>")[0],
                    account({"platformFeeRate": 0.5})[0],
                    account({"platformFeeRate": "0.005"})[0]):
            code, out, err = run(helper(acp), *CLOSE)
            self.assertEqual(code, 1)
            self.assertEqual(out, "")
            self.assertIn("could not read the Virtuals platform fee", err)

    def test_every_total_carries_it(self):
        back, _ = self.quote({"platformFeeRate": 0.005}, "--side", "buyback", "--instrument", ETH_CALL,
                             "--size", "1", "--premium-received", "60")
        self.assertEqual((back["fee_usd"], back["platform_fee_usd"]), (1.35, 0.25))
        self.assertEqual(back["total_cost_usd"], 51.35)  # 50 + 1.10 + 0.25
        self.assertEqual(back["result_usd"], 8.65)

    def test_a_derive_quote_carries_the_order_managers_settings(self):
        buy, _ = self.quote({"platformFeeRate": 0}, "--side", "buy", "--product", "call", "--underlying", "ETH",
                            "--size", "1", "--strike", "1900")
        # Worked, a buy may pay what the ordinary one may: its $53.66 ceiling, $52.50 a
        # contract on the tick; the receipt still measures against today's $50 ask.
        self.assertEqual(buy["worked"], {
            "params": {"INSTRUMENT": ETH_CALL, "ACTION": "buy", "SIZE": 1.0, "WORST_PRICE": 52.5,
                       "FEE_USD": 1.1, "SIZE_STEP": 0.01, "MIN_SIZE": 0.01, "TICK_SIZE": 0.1,
                       "MAKER_FEE_RATE": 0.0001, "FILL_NOW_PRICE": 50.0},
            "fund_usdc": 55, "at_mark_saves_usd": 1.0,
            # $1 to the mark, plus the $1.10 taker fee less the $0.20 maker fee
            "saves_up_to_usd": 1.9, "saves_up_to_pct": 3.8, "price_saves_usd": 1.0,
            "fee_saves_usd": 0.9, "ask_over_fair_pct": 2.0, "recommended": False})
        back, _ = self.quote({"platformFeeRate": 0}, *CLOSE[1:])
        self.assertEqual((back["worked"]["params"]["ACTION"], back["worked"]["params"]["WORST_PRICE"],
                          back["worked"]["fund_usdc"], back["worked"]["at_mark_saves_usd"]),
                         ("close", 48.0, 0, 1.0))

    def test_the_parts_add_up_to_the_fee(self):
        h = helper(account()[0])
        h.PLATFORM["rate"] = 0.005
        for premium, venue in ((18.22, 0.704), (5.0, 0.6234), (77.6, 0.561685)):
            parts = h.fee_fields(venue, h.platform_fee(premium))
            self.assertAlmostEqual(parts["venue_fee_usd"] + parts["platform_fee_usd"], parts["fee_usd"], places=9)

    def test_a_budget_buys_less_once_the_platform_fee_is_counted(self):
        args = ("--side", "buy", "--product", "call", "--underlying", "ETH", "--budget", "53.66", "--strike", "1900")
        free, _ = self.quote({"platformFeeRate": 0}, *args)
        paid, _ = self.quote({"platformFeeRate": 0.005}, *args)
        self.assertEqual(free["platform_fee_usd"], 0)
        self.assertEqual((free["size"], paid["size"]), (1, 0.99))
        self.assertEqual(paid["total_cost_usd"], round(paid["premium_usd"] + paid["fee_usd"], 2))
        self.assertLessEqual(paid["max_cost_usd"], 53.66)

    def test_paradex_and_reads_that_price_nothing_never_ask(self):
        for argv in (("quote", "--venue", "paradex", "--side", "close", "--instrument", "X", "--size", "1"),
                     ("chain", "--underlying", "ETH"),
                     ("minimum", "--underlying", "ETH")):
            acp, calls = account({"platformFeeRate": 0.005})
            h = helper(acp)
            h.run_quote = lambda p, a: {}
            h.chain_rows = h.build_minimum = lambda *a, **k: {}
            run(h, *argv)
            self.assertEqual(calls, [], argv)
            self.assertEqual(h.PLATFORM["rate"], 0.0)

    def test_there_is_no_flag(self):
        code, _, err = run(helper(account({"platformFeeRate": 0})[0]), *CLOSE, "--platform-fee-rate", "0")
        self.assertEqual(code, 2)
        self.assertIn("unrecognized arguments", err)


class FirstTimeCheckTest(unittest.TestCase):
    """The server keeps no history: an account holding no option of the kind asks first."""

    BUY = ("quote", "--side", "buy", "--product", "call", "--underlying", "ETH", "--strike", "1900", "--size", "1")

    def quote(self, positions, *argv):
        h = helper(account({"platformFeeRate": 0, "account": {"exists": True, "positions": positions}})[0])
        code, out, err = run(h, *argv)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def test_no_bought_option_asks_the_three_questions(self):
        q = self.quote([{"instrument": "ETH-20261225-1500-P", "size": -0.1}], *self.BUY)
        self.assertEqual(len(q["first_time_check"]["questions"]), 3)
        self.assertIn("ETH ends past the breakeven", q["first_time_check"]["questions"][1])

    def test_a_bought_option_held_skips_them(self):
        q = self.quote([{"instrument": ETH_CALL, "size": "0.5"}], *self.BUY)
        self.assertNotIn("first_time_check", q)

    def test_paradex_is_not_read_so_carries_none(self):
        h = helper(account({"platformFeeRate": 0})[0])
        self.assertEqual(h.first_time_check("buy", "ETH"), {})


class WorkedSavingTest(unittest.TestCase):
    """What the order manager could save, as the offer says it: the price and the fee."""

    def quote(self, ticker, *argv, rate=0.0):
        h = helper(account({"platformFeeRate": rate})[0])
        h.tickers_for = lambda cur, expiry: {ETH_CALL: ticker}
        code, out, err = run(h, "quote", *argv)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    BUY = ("--side", "buy", "--product", "call", "--underlying", "ETH", "--strike", "1900")

    def test_an_ask_at_the_mark_still_saves_the_fee(self):
        w = self.quote(dict(TICKER, a="49"), *self.BUY, "--size", "10")["worked"]
        # 0.5 + 0.0003 x 2000 x 10 = $6.50 taking; 0.0001 x 2000 x 10 = $2.00 resting
        self.assertEqual((w["at_mark_saves_usd"], w["price_saves_usd"], w["fee_saves_usd"]), (0, 0, 4.5))
        self.assertEqual((w["saves_up_to_usd"], w["saves_up_to_pct"]), (4.5, 0.9))

    def test_a_bid_past_the_mark_caps_the_price_a_tick_above_it(self):
        w = self.quote(dict(TICKER, b="49.5"), *self.BUY, "--size", "1")["worked"]
        self.assertEqual(w["at_mark_saves_usd"], 1.0)
        self.assertEqual(w["price_saves_usd"], 0.4)  # 50 - 49.6, not 50 - 49

    def test_the_bound_and_its_fee_fit_the_ceiling_and_the_wallet(self):
        for rate in (0, 0.005):
            q = self.quote(TICKER, *self.BUY, "--budget", "500", rate=rate)
            p, w = q["worked"]["params"], q["worked"]
            self.assertGreaterEqual(p["WORST_PRICE"], q["ask_price"])
            self.assertEqual(p["FILL_NOW_PRICE"], q["ask_price"])
            need = p["WORST_PRICE"] * p["SIZE"] + p["FEE_USD"]
            self.assertLessEqual(need, q["max_cost_usd"] + 0.01)
            self.assertGreaterEqual(w["fund_usdc"], need + min(need * 0.02, 2))

    def test_a_close_cannot_rest_so_saves_no_fee(self):
        w = self.quote(TICKER, *CLOSE[1:])["worked"]
        self.assertEqual((w["fee_saves_usd"], w["price_saves_usd"], w["saves_up_to_usd"]), (0, 1.0, 1.0))
        self.assertNotIn("FILL_NOW_PRICE", w["params"])

    def test_a_big_buy_well_over_fair_value_recommends_the_order_manager(self):
        w = self.quote(dict(TICKER, a="52"), *self.BUY, "--size", "20")["worked"]  # $1,040, 6.1% over
        self.assertEqual((w["recommended"], w["ask_over_fair_pct"]), (True, 6.1))

    def test_a_small_buy_or_one_near_fair_value_does_not(self):
        near = self.quote(TICKER, *self.BUY, "--size", "25")["worked"]  # $1,250, 2% over
        self.assertEqual((near["recommended"], near["ask_over_fair_pct"]), (False, 2.0))
        small = self.quote(dict(TICKER, a="52"), *self.BUY, "--size", "1")["worked"]  # $52, 6.1% over
        self.assertFalse(small["recommended"])

    def test_the_owners_lower_ceiling_bounds_the_order_manager(self):
        base = self.quote(TICKER, *self.BUY, "--budget", "500", rate=0.005)
        own = round(base["total_cost_usd"] - 5, 2)  # under today's price
        q = self.quote(TICKER, *self.BUY, "--budget", "500", "--max-cost", str(own), rate=0.005)
        p, w = q["worked"]["params"], q["worked"]
        self.assertEqual(q["max_cost_usd"], own)
        self.assertLess(p["WORST_PRICE"], q["ask_price"])
        self.assertLessEqual(p["WORST_PRICE"] * p["SIZE"] + p["FEE_USD"], own)
        self.assertEqual(p["FILL_NOW_PRICE"], q["ask_price"])
        self.assertLessEqual(w["fund_usdc"], own + 2 + 1)
        self.assertTrue(any("will not fill" in x for x in q["warnings"]), q["warnings"])
        self.assertIn("so pick one", q["route_question"])

    def test_the_owners_higher_ceiling_is_carried_too(self):
        q = self.quote(TICKER, *self.BUY, "--size", "10", "--max-cost", "600")
        p = q["worked"]["params"]
        self.assertEqual(q["max_cost_usd"], 600)
        self.assertGreater(p["WORST_PRICE"] * p["SIZE"], 0.95 * 600 - p["FEE_USD"])
        self.assertLessEqual(p["WORST_PRICE"] * p["SIZE"] + p["FEE_USD"], 600)
        self.assertFalse(any("will not fill" in x for x in q["warnings"]))

    def test_max_cost_is_a_buy_flag_never_over_the_budget(self):
        h = helper(account({"platformFeeRate": 0})[0])
        code, _, err = run(h, "quote", *self.BUY, "--budget", "500", "--max-cost", "501")
        self.assertEqual(code, 2, err)
        code, _, err = run(helper(account({"platformFeeRate": 0})[0]), "quote", *CLOSE[1:], "--max-cost", "5")
        self.assertEqual(code, 2, err)

    def test_the_route_question_says_what_a_plain_yes_takes(self):
        book = self.quote(TICKER, *self.BUY, "--size", "10")
        self.assertIn("buys now from the order book", book["route_question"])
        big = self.quote(dict(TICKER, a="52"), *self.BUY, "--size", "20")
        self.assertIn("starts the order manager", big["route_question"])

    def test_a_main_wallet_short_of_the_funding_is_never_recommended(self):
        h = helper(account({"platformFeeRate": 0, "cashUsd": 61.81})[0])
        h.tickers_for = lambda cur, expiry: {ETH_CALL: dict(TICKER, a="52")}
        code, out, err = run(h, "quote", *self.BUY, "--size", "20")
        self.assertEqual(code, 0, err)
        q = json.loads(out)
        w = q["worked"]
        self.assertFalse(w["recommended"])
        self.assertEqual(w["wallet_cash_usd"], 61.81)
        self.assertEqual(w["wallet_short_usd"], int(-(-(w["fund_usdc"] - 61.81) // 1)))
        self.assertIn("buys now from the order book", q["route_question"])

    def test_a_funded_main_wallet_keeps_it(self):
        h = helper(account({"platformFeeRate": 0, "cashUsd": 5000})[0])
        h.tickers_for = lambda cur, expiry: {ETH_CALL: dict(TICKER, a="52")}
        code, out, err = run(h, "quote", *self.BUY, "--size", "20")
        w = json.loads(out)["worked"]
        self.assertTrue(w["recommended"])
        self.assertNotIn("wallet_short_usd", w)

    def test_paradex_is_never_worked(self):
        h = helper(account({"platformFeeRate": 0})[0])
        self.assertEqual(h.worked("buy", ETH_CALL, INST, 1, 50, 1, 49), {"worked": h.worked(
            "buy", ETH_CALL, INST, 1, 50, 1, 49)["worked"]})
        h.V = {"id": "paradex", "name": "Paradex"}
        self.assertEqual(h.worked("buy", ETH_CALL, INST, 1, 50, 1, 49), {})


if __name__ == "__main__":
    unittest.main()
