#!/usr/bin/env python3
"""Daily market watchlist email.

Pulls the top 10 stocks and top 10 cryptocurrencies by social/market momentum
from the LunarCrush API, attaches recent news headlines per asset, and emails
an HTML digest.

NOT FINANCIAL ADVICE. This is automated research to inform your own decisions.

Required environment variables:
  LUNARCRUSH_API_KEY  LunarCrush API key (lunarcrush.com/developers)
  MAIL_USERNAME       Gmail address used to send (SMTP login)
  MAIL_APP_PASSWORD   Gmail app password (myaccount.google.com/apppasswords)
Optional:
  TO_EMAIL            Recipient (defaults to MAIL_USERNAME)

Run with --dry-run to print the digest instead of sending it.
"""

import html
import json
import os
import smtplib
import sys
import urllib.parse
import urllib.request
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

API_BASE = "https://lunarcrush.com/api4/public"

# Liquidity floors so the digest surfaces tradeable assets, not micro-cap noise
# that tops the raw social charts.
STOCK_MIN_MCAP = 2e9
COIN_MIN_MCAP = 5e8
MIN_INTERACTIONS = 10_000

DISCLAIMER = (
    "This is automated research, not financial advice. It is not a "
    "solicitation and returns are never guaranteed; markets are risky and you "
    "can lose money. Do your own due diligence and consider a licensed "
    "financial professional before investing."
)


def api_get(path):
    req = urllib.request.Request(
        API_BASE + path,
        headers={
            "Authorization": "Bearer " + os.environ["LUNARCRUSH_API_KEY"],
            "User-Agent": "daily-market-email/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def top_assets(kind, min_mcap, count=10):
    """Top `count` assets: fetch the social-interaction leaders, filter for
    liquidity, then rank by LunarCrush AltRank (lower = stronger momentum)."""
    rows = api_get(f"/{kind}/list/v1?sort=interactions_24h&limit=100")["data"]
    liquid = [
        r
        for r in rows
        if num(r.get("market_cap")) >= min_mcap
        and (r.get("interactions_24h") or 0) >= MIN_INTERACTIONS
    ]
    liquid.sort(key=lambda r: r.get("alt_rank") or 10**9)
    return liquid[:count]


def asset_news(topic, count=2):
    """Recent news headlines for an asset topic; empty list on any failure."""
    if not topic:
        return []
    try:
        data = api_get(f"/topic/{urllib.parse.quote(topic)}/news/v1")["data"]
    except Exception:
        return []
    return [
        {"title": p.get("post_title") or "", "url": p.get("post_link") or ""}
        for p in data[:count]
        if p.get("post_link")
    ]


def fmt_price(value):
    p = num(value)
    if p >= 1000:
        return f"${p:,.0f}"
    if p >= 1:
        return f"${p:,.2f}"
    return f"${p:.4f}"


def rows_html(assets):
    out = []
    for r in assets:
        change = num(r.get("percent_change_24h"))
        color = "#15803d" if change >= 0 else "#b91c1c"
        news = asset_news(r.get("topic"))
        links = " &middot; ".join(
            f'<a href="{html.escape(n["url"])}">{html.escape(n["title"][:80])}</a>'
            for n in news
        ) or "&mdash;"
        out.append(
            "<tr>"
            f"<td><b>{html.escape(str(r.get('symbol', '')))}</b><br>"
            f"<small>{html.escape(str(r.get('name', ''))[:32])}</small></td>"
            f"<td align='right'>{fmt_price(r.get('price'))}</td>"
            f"<td align='right' style='color:{color}'>{change:+.2f}%</td>"
            f"<td align='right'>{num(r.get('galaxy_score')):.0f}</td>"
            f"<td align='right'>{r.get('alt_rank', '')}</td>"
            f"<td>{links}</td>"
            "</tr>"
        )
    return "\n".join(out)


def build_digest():
    stocks = top_assets("stocks", STOCK_MIN_MCAP)
    coins = top_assets("coins", COIN_MIN_MCAP)
    table_head = (
        "<tr><th align='left'>Asset</th><th align='right'>Price</th>"
        "<th align='right'>24h</th><th align='right'>Galaxy</th>"
        "<th align='right'>AltRank</th><th align='left'>Recent news</th></tr>"
    )
    style = (
        "font-family:Arial,sans-serif;font-size:14px;border-collapse:collapse;"
        "width:100%"
    )
    return f"""\
<html><body style="font-family:Arial,sans-serif;color:#111">
<p style="background:#fef3c7;padding:10px;border-radius:6px">
&#9888;&#65039; <b>Not financial advice.</b> {DISCLAIMER}</p>
<h2>Top 10 stocks to watch &mdash; {date.today():%B %d, %Y}</h2>
<p><small>Momentum leaders (LunarCrush AltRank, lower is stronger) among
liquid names with real social volume. Galaxy = LunarCrush Galaxy Score
(0&ndash;100 combined social + market health).</small></p>
<table border="1" cellpadding="6" style="{style}">{table_head}
{rows_html(stocks)}</table>
<h2>Top 10 cryptocurrencies to watch</h2>
<table border="1" cellpadding="6" style="{style}">{table_head}
{rows_html(coins)}</table>
<p><small>High social momentum is a short-term signal, not a fundamentals
signal &mdash; verify every name before acting. {DISCLAIMER}</small></p>
</body></html>
"""


def main():
    digest = build_digest()
    if "--dry-run" in sys.argv:
        print(digest)
        return
    sender = os.environ["MAIL_USERNAME"]
    recipient = os.environ.get("TO_EMAIL") or sender
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily watchlist: top 10 stocks & crypto — {date.today():%b %d, %Y}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(digest, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, os.environ["MAIL_APP_PASSWORD"])
        smtp.sendmail(sender, [recipient], msg.as_string())
    print(f"Sent digest to {recipient}")


if __name__ == "__main__":
    main()
