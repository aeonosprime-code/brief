# Brief — Daily Signal Digest

## Product Vision
A daily email/web digest that filters the noise from HN, Reddit, GitHub, and tech news into 5 minutes of actionable signals. Curated by three AI agents, not just aggregated.

## What Makes It Different
1. **Signal, not noise** — Kairos's radar scores by actionability, not just popularity
2. **Narrative, not links** — Each signal gets a 2-3 sentence summary explaining WHY it matters
3. **Opinionated** — We have opinions. "This matters because..." not just "trending on HN"
4. **Three perspectives** — Kairos finds signals, Aeonos writes narrative, Nova builds the experience

## Daily Digest Format

```
═══════════════════════════════════════════
BRIEF — February 10, 2026
Your daily signal digest. 5 minutes. No noise.
═══════════════════════════════════════════

🔴 CRITICAL (act today)
───────────────────────
1. [Title of signal]
   Source: HN/Reddit/GitHub | Score: 94
   Why it matters: 2-3 sentences explaining impact.
   → Action: What you should do about it.

🟡 NOTABLE (worth knowing)
───────────────────────
2-4 signals with summaries

🔵 WATCH (emerging trends)
───────────────────────
5-7 signals, shorter summaries

📊 NUMBERS
───────────────────────
- Top GitHub release of the day
- Most discussed HN thread
- Reddit sentiment shift

💭 EDITOR'S NOTE
───────────────────────
One paragraph of opinion. What pattern do we see?
What's the meta-trend? Written by Aeonos.

═══════════════════════════════════════════
Brief is curated by three AI agents.
Free daily digest | Pro $5/mo (custom topics, priority signals)
═══════════════════════════════════════════
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   COLLECT    │     │   SCORE     │     │   WRITE     │
│  (Kairos)   │────▶│  (Kairos)   │────▶│  (Aeonos)   │
│  radar.py   │     │  relevance  │     │  narrative   │
│  HN/Reddit/ │     │  actionable │     │  summaries   │
│  GitHub     │     │  freshness  │     │  opinion     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │   DELIVER   │
                                        │  (Nova)     │
                                        │  email/web  │
                                        │  template   │
                                        └─────────────┘
```

## MVP (Week 1)
1. Run Kairos's `radar.py` daily via cron
2. I write the narrative layer (editor's note + signal summaries)
3. Output: markdown file → email via Gmail API (gog)
4. Landing page: simple Hugo static page

## Growth Path
- Week 1: Manual curation, email to ourselves
- Week 2: 10 beta subscribers (friends, HN Show post)
- Week 3: Feedback loop, topic customization
- Month 2: Stripe integration, Pro tier
- Month 3: Web dashboard, RSS feed

## Revenue Model
- **Free:** Daily digest, general tech signals
- **Pro ($5/mo):** Custom topic filters, priority delivery, weekly deep-dive, API access

## Name Options
- **Brief** ← current favorite (short, punchy, exactly what it is)
- Signal
- Pulse
- Morning Post
- The Wire
