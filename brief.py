#!/usr/bin/env python3
"""brief.py — Generate a daily signal digest from HN + GitHub Trending.
v2: Cleaned up after 3 weeks of production use.

Usage: python3 brief.py [output.md]
"""

import json
import urllib.request
import time
import datetime
import sys
import os
import re

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else None
TODAY = datetime.date.today().isoformat()


def fetch_json(url, headers=None, timeout=10):
    """Fetch JSON from a URL with error handling."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Brief/2.0 (by aeonos)")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Warn: {url} -> {e}", file=sys.stderr)
        return None


def fetch_html(url, timeout=10):
    """Fetch raw HTML."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Brief/2.0 (by aeonos)")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Warn: {url} -> {e}", file=sys.stderr)
        return None


def truncate(text, limit=120):
    """Truncate text at word boundary."""
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(' ', 1)[0]
    return cut + "…"


def collect_hn(limit=15, min_score=50):
    """Fetch top HN stories above score threshold."""
    print("Fetching HN top stories...", file=sys.stderr)
    ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        return []
    stories = []
    for sid in ids[:limit]:
        data = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if not data or data.get("type") != "story":
            continue
        score = data.get("score", 0)
        if score < min_score:
            continue
        stories.append({
            "title": data.get("title", ""),
            "score": score,
            "url": data.get("url") or f"https://news.ycombinator.com/item?id={sid}",
            "discussion": f"https://news.ycombinator.com/item?id={sid}",
            "engagement": data.get("descendants", 0),
            "source": "HN",
        })
        time.sleep(0.1)
    print(f"  Got {len(stories)} HN stories", file=sys.stderr)
    return stories


def collect_github_trending(max_results=8):
    """Fetch GitHub trending repos (daily)."""
    print("Fetching GitHub Trending...", file=sys.stderr)
    html = fetch_html("https://github.com/trending?since=daily")
    if not html:
        return []

    repos = []
    articles = re.split(r'<article', html)

    for article in articles[1:]:
        repo_match = re.search(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"', article)
        if not repo_match:
            continue
        repo_path = repo_match.group(1).strip()
        if repo_path.count("/") != 2 or not repo_path.startswith("/"):
            continue

        # Description
        desc = ""
        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', article, re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # Stars today (ranking signal)
        stars_today = 0
        stars_match = re.search(r'(\d[\d,]*)\s+stars?\s+today', article)
        if stars_match:
            stars_today = int(stars_match.group(1).replace(",", ""))

        # Total stars (display only)
        total_stars = 0
        total_match = re.search(r'href="/[^"]+/stargazers"[^>]*>\s*(?:<[^>]*>\s*)*(\d[\d,]*)', article)
        if total_match:
            total_stars = int(total_match.group(1).replace(",", ""))

        title = repo_path.lstrip("/")
        if desc:
            title = f"{title} — {truncate(desc, 100)}"

        repos.append({
            "title": title,
            "score": stars_today if stars_today > 0 else max(total_stars // 100, 50),
            "url": f"https://github.com{repo_path}",
            "discussion": f"https://github.com{repo_path}",
            "engagement": total_stars,  # Display as stars, not comments
            "source": "GitHub",
        })

    repos.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Got {len(repos)} trending repos", file=sys.stderr)
    return repos[:max_results]


def dedup_signals(signals):
    """Remove cross-source duplicates (same URL or very similar titles)."""
    seen_urls = set()
    seen_titles = set()
    deduped = []
    for s in signals:
        url_key = s["url"].rstrip("/").lower()
        title_key = s["title"].lower().strip()[:60]
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        deduped.append(s)
    return deduped


def format_digest(signals):
    """Format signals into Brief digest with tiered ranking."""
    signals.sort(key=lambda x: x["score"], reverse=True)

    critical = signals[:3]
    notable = signals[3:7]
    watch = signals[7:12]

    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")

    def engagement_label(s):
        """Human-readable engagement metric."""
        if s["source"] == "GitHub":
            return f"⭐ {s['engagement']:,} stars"
        else:
            return f"{s['engagement']} comments"

    lines = [
        f"# BRIEF — {TODAY}",
        f"*Your daily signal digest. 5 minutes. No noise.*",
        "",
        "---",
        "",
    ]

    if critical:
        lines.append("## 🔴 CRITICAL")
        lines.append("")
        for s in critical:
            lines.append(f"**[{s['title']}]({s['url']})**")
            lines.append(f"*{s['source']} • {s['score']} points, {engagement_label(s)}*")
            lines.append(f"[Discuss]({s['discussion']})")
            lines.append("")
        lines.append("---")
        lines.append("")

    if notable:
        lines.append("## 🟡 NOTABLE")
        lines.append("")
        for s in notable:
            lines.append(f"**[{s['title']}]({s['url']})**")
            lines.append(f"*{s['source']} • {s['score']} points, {engagement_label(s)}*")
            lines.append(f"[Discuss]({s['discussion']})")
            lines.append("")
        lines.append("---")
        lines.append("")

    if watch:
        lines.append("## 🔵 WATCH")
        lines.append("")
        for s in watch:
            lines.append(f"- **{s['title']}** — *{s['source']}, {s['score']} pts, {engagement_label(s)}*")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 💭 EDITOR'S NOTE")
    lines.append("")
    lines.append("*[Aeonos — write your editorial after reviewing the signals above]*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Brief is collected by Aeonos. Solo operation.*")
    lines.append(f"*Generated: {now}*")

    return "\n".join(lines)


def main():
    hn = collect_hn(limit=15, min_score=50)
    github = collect_github_trending(max_results=8)

    signals = hn + github
    signals = dedup_signals(signals)

    print(f"\nTotal signals: {len(signals)} (after dedup)", file=sys.stderr)

    if not signals:
        print("No signals collected. Check connectivity.", file=sys.stderr)
        sys.exit(1)

    digest = format_digest(signals)

    out_path = OUTPUT
    if not out_path:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"brief-{TODAY}.md")

    with open(out_path, "w") as f:
        f.write(digest)

    print(f"Done: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
