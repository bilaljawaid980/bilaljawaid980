import os
import datetime as dt
from collections import defaultdict

import requests
import matplotlib.pyplot as plt
import imageio.v2 as imageio

USER = os.getenv("GH_USER", "bilaljawaid980")
TOKEN = os.getenv("GH_TOKEN", "")

OUT_DIR = "assets"
OUT_GIF = os.path.join(OUT_DIR, "activity.gif")

DAYS = 30  # last 30 days
PAGES = 3  # fetch a few pages of events


def fetch_events():
    headers = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    events = []
    for page in range(1, PAGES + 1):
        url = f"https://api.github.com/users/{USER}/events/public?per_page=100&page={page}"
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        events.extend(batch)
    return events


def count_by_day(events, start_date, end_date):
    counts = defaultdict(int)
    for e in events:
        ts = e.get("created_at")
        if not ts:
            continue
        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        if start_date <= t <= end_date:
            counts[t] += 1

    days = []
    vals = []
    cur = start_date
    while cur <= end_date:
        days.append(cur)
        vals.append(counts[cur])
        cur += dt.timedelta(days=1)
    return days, vals


def render_frames(days, vals):
    # Create an animation by progressively drawing the line
    frames = []
    n = len(days)

    x = list(range(n))
    y = vals

    for k in range(1, n + 1):
        fig = plt.figure(figsize=(7.5, 2.2), dpi=140)
        ax = fig.add_subplot(111)

        ax.plot(x[:k], y[:k], linewidth=2)
        ax.fill_between(x[:k], y[:k], alpha=0.2)

        ax.set_xlim(0, n - 1)
        ax.set_ylim(0, max(1, max(y) + 1))

        ax.set_xticks([0, n // 2, n - 1])
        ax.set_xticklabels([
            days[0].strftime("%d %b"),
            days[n // 2].strftime("%d %b"),
            days[-1].strftime("%d %b"),
        ])

        ax.set_yticks([0, max(1, max(y))])
        ax.set_title(f"{USER} — last {DAYS} days activity", fontsize=10)

        ax.grid(True, alpha=0.25)
        for spine in ax.spines.values():
            spine.set_alpha(0.25)

        fig.tight_layout()

        # Convert plot to image array
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        img = (plt.imread(fig.canvas.buffer_rgba(), format="raw")
               if hasattr(fig.canvas, "buffer_rgba") else None)

        # Fallback approach using canvas buffer
        buf = fig.canvas.tostring_rgb()
        img = imageio.imread(buf, format="RGB", size=(h, w, 3))

        plt.close(fig)
        frames.append(img)

    # Add a short hold at the end
    frames.extend([frames[-1]] * 12)
    return frames


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=DAYS - 1)
    end = today

    events = fetch_events()
    days, vals = count_by_day(events, start, end)

    frames = render_frames(days, vals)

    # Save GIF
    imageio.mimsave(OUT_GIF, frames, duration=0.06)  # ~60ms per frame
    print(f"Saved: {OUT_GIF}")


if __name__ == "__main__":
    main()
