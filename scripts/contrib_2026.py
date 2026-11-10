"""Render the user's 2026 contribution calendar as an animated SVG (light + dark)."""
import json
import os
import subprocess

USER = os.environ.get("GH_USER", "abhinavchutani")
YEAR = 2026
CELL, GAP, PAD, TOP = 13, 4, 16, 40
STEP = CELL + GAP

QUERY = (
    "query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){"
    "contributionsCollection(from:$from,to:$to){contributionCalendar{"
    "weeks{contributionDays{contributionCount date weekday}}}}}}"
)

PALETTES = {
    "dark": {"bg": "#0d1117", "text": "#c9d1d9", "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]},
    "light": {"bg": "#ffffff", "text": "#24292f", "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]},
}


def fetch_weeks():
    out = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={QUERY}",
            "-f", f"login={USER}",
            "-f", f"from={YEAR}-01-01T00:00:00Z",
            "-f", f"to={YEAR}-12-31T23:59:59Z",
        ],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def level(count, peak):
    if count == 0 or peak == 0:
        return 0
    ratio = count / peak
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def render(weeks, theme):
    pal = PALETTES[theme]
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0)
    total = sum(d["contributionCount"] for w in weeks for d in w["contributionDays"])
    width = PAD * 2 + len(weeks) * STEP
    height = TOP + 7 * STEP + PAD
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".c{animation:glow 6s ease-in-out infinite}",
        "@keyframes glow{0%,100%{opacity:.35}50%{opacity:1}}",
        f".t{{font:600 16px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:{pal['text']}}}",
        "</style>",
        f'<rect width="{width}" height="{height}" rx="10" fill="{pal["bg"]}"/>',
        f'<text class="t" x="{PAD}" y="{PAD + 12}">{YEAR} contributions</text>',
    ]
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            lv = level(day["contributionCount"], peak)
            x = PAD + wi * STEP
            y = TOP + day["weekday"] * STEP
            delay = -(wi * 0.18)  # negative delay: the glow sweeps left to right across the year
            parts.append(
                f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{pal["levels"][lv]}" style="animation-delay:{delay:.2f}s"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts), total


def main():
    weeks = fetch_weeks()
    for theme in PALETTES:
        svg, total = render(weeks, theme)
        path = f"assets/contrib-{YEAR}-{theme}.svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({total} contributions)")


if __name__ == "__main__":
    main()
