# Claude Code Agents

Custom subagents for this repository. Each `*.md` file defines one agent
(YAML frontmatter + a system prompt).

## investment-scout

Researches **stocks and cryptocurrencies** for long-term (12+ months) and
short-term (days–months) opportunities.

### How to run it

From a Claude Code session in this repo, ask Claude to delegate to it:

- "Use the investment-scout agent to find promising stocks and crypto."
- "Have investment-scout give me a long-term and short-term watchlist."
- "Ask investment-scout what it thinks about NVDA and ETH."

Claude will launch the subagent, which returns its research to the main
conversation.

### What it does

- Pulls social/market-momentum data from the **LunarCrush** tools
  (`stocks`, `cryptocurrencies`, `list`, `search`, `topic`,
  `topic_time_series`).
- Grounds every candidate in recent news, earnings, and catalysts via
  **WebSearch / WebFetch** — it does not act on social hype alone.
- Returns ideas split into **Long-term** and **Short-term** tables, each with a
  thesis, key risks, and an "invalidated if…" line, plus responsible-investing
  guidance.

### Requirements

The LunarCrush MCP server must be available in the session for the momentum
data. Without it, the agent falls back to web research only and will say so.

### ⚠️ Not financial advice

This agent produces **research to inform your own decisions** — not financial
advice, not a solicitation, and not a guarantee of returns. No tool can reliably
predict markets; you can lose money. Do your own due diligence and consider a
licensed financial professional before investing.
