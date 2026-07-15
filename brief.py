#!/usr/bin/env python3
"""brief.py — Generate a daily signal digest from HN + Reddit.
Solo version. Collects, formats, ready for editorial.

Usage: python3 brief.py [output.md]
"""

import json
import urllib.request
import time
import datetime
import sys
import os

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else None

def fetch_json(url, headers=None):
    req = urllib.request.Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    req.add_header("User-Agent", "Brief/1.0 (by aeonos)")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Warn: {url} -> {e}", file=sys.stderr)
        return None

def collect_hn(limit=15, min_score=50):
    """Fetch top HN stories."""
    print("Fetching HN top stories...", file=sys.stderr)
    ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        return []
    stories = []
    for sid in ids[:limit]:
        data = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if data and data.get("type") == "story" and data.get("score", 0) >= min_score:
            stories.append({
                "title": data.get("title", ""),
                "score": data.get("score", 0),
                "url": data.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                "discussion": f"https://news.ycombinator.com/item?id={sid}",
                "comments": data.get("descendants", 0),
                "source": "HN",
            })
        time.sleep(0.1)
    stories.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Got {len(stories)} HN stories", file=sys.stderr)
    return stories

def collect_reddit_rss(subreddits, limit=5):
    """Fetch top posts from subreddits via RSS (JSON API blocks server IPs)."""
    import xml.etree.ElementTree as ET
    all_posts = []
    for sub in subreddits:
        print(f"  r/{sub} (RSS)...", file=sys.stderr)
        url = f"https://www.reddit.com/r/{sub}/top.rss?t=day&limit={limit}"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Brief/1.0 (by aeonos)")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read().decode("utf-8", errors="replace")
            root = ET.fromstring(xml_data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:limit]:
                title_el = entry.find("atom:title", ns)
                link_el = entry.find("atom:link", ns)
                title = title_el.text if title_el is not None else ""
                link = link_el.get("href", "") if link_el is not None else ""
                if title and link:
                    all_posts.append({
                        "title": title,
                        "score": 50,  # RSS doesn't expose score; assign baseline
                        "url": link,
                        "discussion": link,
                        "comments": 0,
                        "source": f"r/{sub}",
                    })
        except Exception as e:
            print(f"  Warn: r/{sub} RSS -> {e}", file=sys.stderr)
        time.sleep(5)  # Reddit rate-limits aggressively
    print(f"  Got {len(all_posts)} Reddit posts via RSS", file=sys.stderr)
    return all_posts

def collect_reddit(subreddits, limit=5, min_score=20):
    """Fetch top posts from subreddits."""
    all_posts = []
    for sub in subreddits:
        print(f"  r/{sub}...", file=sys.stderr)
        data = fetch_json(f"https://www.reddit.com/r/{sub}/top.json?t=day&limit={limit}")
        if data and "data" in data and "children" in data["data"]:
            for child in data["data"]["children"]:
                p = child["data"]
                if p.get("score", 0) >= min_score:
                    all_posts.append({
                        "title": p.get("title", ""),
                        "score": p.get("score", 0),
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "discussion": f"https://reddit.com{p.get('permalink', '')}",
                        "comments": p.get("num_comments", 0),
                        "source": f"r/{sub}",
                    })
        time.sleep(0.5)
    print(f"  Got {len(all_posts)} Reddit posts", file=sys.stderr)
    return all_posts

def format_digest(signals):
    """Format signals into Brief digest."""
    signals.sort(key=lambda x: x["score"], reverse=True)
    
    critical = signals[:3]
    notable = signals[3:7]
    watch = signals[7:12]
    
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    
    lines = [
        f"# BRIEF — {today}",
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
            lines.append(f"*{s['source']} • {s['score']} points, {s['comments']} comments*")
            lines.append(f"[Discuss]({s['discussion']})")
            lines.append("")
        lines.append("---")
        lines.append("")
    
    if notable:
        lines.append("## 🟡 NOTABLE")
        lines.append("")
        for s in notable:
            lines.append(f"**[{s['title']}]({s['url']})**")
            lines.append(f"*{s['source']} • {s['score']} points, {s['comments']} comments*")
            lines.append(f"[Discuss]({s['discussion']})")
            lines.append("")
        lines.append("---")
        lines.append("")
    
    if watch:
        lines.append("## 🔵 WATCH")
        lines.append("")
        for s in watch:
            lines.append(f"- **{s['title']}** — *{s['source']}, {s['score']} pts, {s['comments']} comments*")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("## 💭 EDITOR'S NOTE")
    lines.append("")
    lines.append("*[Aeonos — write your editorial after reviewing the signals above]*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Brief is collected by Aeonos. Solo operation.*")
    lines.append(f"*Generated: {now}*")
    
    return "\n".join(lines)

def collect_github_trending():
    """Fetch GitHub trending via web_fetch (readability mode)."""
    print("Fetching GitHub Trending...", file=sys.stderr)
    # Use web_fetch-style approach: fetch raw HTML, extract repo names and stars
    req = urllib.request.Request("https://github.com/trending?since=daily")
    req.add_header("User-Agent", "Brief/1.0 (by aeonos)")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Warn: GitHub trending -> {e}", file=sys.stderr)
        return []
    
    import re
    repos = []
    # Split by article tags — each trending repo is wrapped in <article>
    articles = re.split(r'<article', html)
    
    for article in articles[1:]:
        # Extract repo path from h2 > a href
        repo_match = re.search(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"', article)
        if not repo_match:
            continue
        repo_path = repo_match.group(1).strip()
        if repo_path.count("/") != 2 or not repo_path.startswith("/"):
            continue
        
        # Extract description
        desc = ""
        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', article, re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
        
        # Extract stars today
        stars_today = 0
        stars_match = re.search(r'(\d[\d,]*)\s+stars?\s+today', article)
        if stars_match:
            stars_today = int(stars_match.group(1).replace(",", ""))
        
        # Extract total stars
        total_stars = 0
        total_match = re.search(r'href="/[^"]+/stargazers"[^>]*>\s*(?:<[^>]*>\s*)*(\d[\d,]*)', article)
        if total_match:
            total_stars = int(total_match.group(1).replace(",", ""))
        
        title = f"{repo_path.lstrip('/')}"
        if desc:
            title += f" — {desc[:100]}"
        
        repos.append({
            "title": title,
            "score": stars_today if stars_today > 0 else (total_stars // 100 if total_stars else 50),
            "url": f"https://github.com{repo_path}",
            "discussion": f"https://github.com{repo_path}",
            "comments": total_stars,
            "source": "GitHub",
        })
    
    repos.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Got {len(repos)} trending repos", file=sys.stderr)
    return repos[:8]

def main():
    hn = collect_hn(limit=15, min_score=50)
    # Reddit blocks server IPs (both JSON API and RSS). Skip silently.
    # When proxy support is added, re-enable collect_reddit_rss.
    reddit = []
    github = collect_github_trending()
    
    signals = hn + reddit + github
    print(f"\nTotal signals: {len(signals)}", file=sys.stderr)
    
    if not signals:
        print("No signals collected. Check connectivity.", file=sys.stderr)
        sys.exit(1)
    
    digest = format_digest(signals)
    
    out_path = OUTPUT
    if not out_path:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"brief-{datetime.date.today().isoformat()}.md")
    
    with open(out_path, "w") as f:
        f.write(digest)
    
    print(f"Done: {out_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
