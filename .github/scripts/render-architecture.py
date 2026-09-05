#!/usr/bin/env python3
# Draws docs/architecture.svg — how a source reaches the Microsoft 365 index.
#
# THIS FILE REPLACES A GENERATOR THAT DID NOT EXIST. docs/index.md pointed at
# diagrams/New-ArchitectureDiagram.ps1, which is not in the repository, so the
# SVG was orphaned and drifted: it showed three sources when there were six push
# tools, and two hosting paths after the scope narrowed to direct push only.
# A diagram nobody can regenerate is a diagram that will drift again.
#
# It answers a different question from connector-tiers.svg. This one is "how does
# a source reach the index, and what else is in the picture"; that one is "what
# does adding a connector cost, and what does it inherit free".
#
#   render-architecture.py <out.svg>
import sys, pathlib, html

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/architecture.svg")
NAVY, DEEP, ORANGE = "#0A3B68", "#072C4E", "#EE7623"
GREEN, RED, MUTED = "#4C9A51", "#C0453A", "#55636F"
INK, RULE, ALT, WHITE, GROUND = "#1B2733", "#D4DCE4", "#E8EEF5", "#FFFFFF", "#F4F7FA"
W, H = 1820, 1120

SOURCES = [
    ("SQL Server — tickets", "SELECT on a view, least privilege"),
    ("SQL Server — hierarchy", "Customers, engagements, time"),
    ("Cloudera CDP", "HDFS · Hive · Atlas catalogue"),
    ("Oracle", "A records view"),
    ("Teradata", "The text minority of a warehouse"),
    ("MongoDB", "A collection, or a GridFS bucket"),
]
TOOLS = ["SqlGraphPush", "SqlHierarchyPush", "CdpGraphPush",
         "OracleGraphPush", "TeradataGraphPush", "MongoGraphPush"]

p = []
def esc(t): return html.escape(t, quote=False)
def rect(x, y, w, h, fill=WHITE, stroke=RULE, sw=1.2, rx=4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="{sw}"{d}/>')
def text(x, y, s, size=13, fill=INK, weight="400", anchor="start", mono=False):
    fam = "IBM Plex Mono, ui-monospace, Menlo, monospace" if mono else \
          "IBM Plex Sans, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    p.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{fill}" '
             f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')
def zone(x, y, w, h, label, sub):
    rect(x, y, w, h, GROUND, RULE, 1)
    text(x + 16, y + 22, label, 11, NAVY, "600")
    text(x + 16, y + 40, sub, 10.5, MUTED)
def arrow(x1, y1, x2, y2, label=None, colour=MUTED):
    p.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{colour}" stroke-width="1.6" '
             f'fill="none" marker-end="url(#a)"/>')
    if label:
        text((x1 + x2) / 2, y1 - 7, label, 9.5, MUTED, anchor="middle", mono=True)

p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-label="How a source reaches the Microsoft 365 index. Six on-premises sources '
         f'— two SQL Server views, a Cloudera CDP cluster holding HDFS, Hive and Atlas, plus Oracle, '
         f'Teradata and MongoDB — are each read by their own console tool. Before any read, a guard '
         f'refuses a source that enforces access per user; SQL Server alone has no such guard. All six '
         f'tools run the shared PushCore engine against a crawl state database that holds the item '
         f'inventory, the run lock and the principal cache, and push straight to the Copilot connectors '
         f'API. Every item is granted one AD group per connector. Microsoft Search and Microsoft 365 '
         f'Copilot read the resulting index, and a read-only dashboard, a health watchdog and an optional '
         f'OTLP collector watch the runs.">')
p.append(f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
         f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>')
rect(0, 0, W, H, GROUND, GROUND, 0, 0)

text(40, 44, "Microsoft 365 Copilot connector platform", 25, NAVY, "600")
p.append(f'<rect x="40" y="56" width="56" height="3" fill="{ORANGE}"/>')
text(40, 82, "Direct push only. Every tool writes to Graph itself; nothing runs behind the Graph connector agent.",
     13, MUTED)

# ---- sources -------------------------------------------------------------
zone(40, 105, 430, 560, "SOURCES", "On premises, never exposed to the cloud")
for i, (name, detail) in enumerate(SOURCES):
    y = 160 + i * 82
    rect(60, y, 390, 66, NAVY, DEEP, 1.2)
    text(76, y + 28, name, 14, WHITE, "600")
    text(76, y + 48, detail, 10.5, "#B9CBDD")
    arrow(455, y + 33, 520, y + 33)

# ---- the guard -----------------------------------------------------------
zone(520, 105, 300, 560, "BEFORE ANY READ", "a source enforcing per user is refused")
rect(540, 160, 260, 190, WHITE, GREEN, 1.4)
text(556, 186, "Guarded", 13, NAVY, "600")
for j, ln in enumerate(["Ranger zones, masks, tag policies",
                        "Oracle VPD, Label Security,", "  Real Application Security, redaction",
                        "Teradata row and column constraints",
                        "Mongo views, encrypted fields"]):
    text(556, 210 + j * 17, "· " + ln if not ln.startswith("  ") else ln, 10, INK)
text(556, 320, "An object the cluster grants to nobody", 10, MUTED)
text(556, 334, "is skipped before its content is read.", 10, MUTED)

rect(540, 372, 260, 92, "#FBEEEC", RED, 1.4)
text(556, 398, "Not guarded", 13, RED, "600")
text(556, 420, "SQL Server: Row-Level Security and", 10, INK)
text(556, 436, "Dynamic Data Masking are not detected.", 10, INK)
text(556, 454, "Scope is the only control — see ACL-1.", 10, RED)
arrow(670, 470, 670, 520)
text(556, 552, "Everything admitted carries ONE", 10.5, NAVY, "600")
text(556, 568, "AD group: the entitlement for", 10.5, NAVY, "600")
text(556, 584, "this source. Control ACL-1.", 10.5, NAVY, "600")
for i in range(6):
    arrow(825, 193 + i * 82, 880, 193 + i * 82)

# ---- the push tools ------------------------------------------------------
zone(880, 105, 420, 560, "THE PUSH TOOLS", "Console apps. One line of Main each")
for i, t in enumerate(TOOLS):
    y = 160 + i * 46
    rect(900, y, 380, 36, ALT, NAVY, 1.1)
    text(916, y + 23, t, 12, NAVY, "600", mono=True)
rect(900, 448, 380, 92, WHITE, NAVY, 1.6)
text(916, 474, "PushCore engine", 14, NAVY, "600")
text(916, 496, "$batch · retry · change detection · delete sweep", 10, INK)
text(916, 512, "(marker, id) checkpoint · redaction · exit codes", 10, INK)
text(916, 530, "One live crawl per connection, by lease", 10, MUTED)
rect(900, 556, 380, 88, WHITE, NAVY, 1.2)
text(916, 582, "Crawl state database", 13, NAVY, "600")
text(916, 602, "Item inventory, run history, the run lock", 10, INK)
text(916, 618, "and the principal cache", 10, INK)
text(916, 636, "Second instance refused, exit 5", 10, MUTED)
# The gap between zones is 55px; a longer label overflows behind the next
# panel, which is how the first render of this file came out.
arrow(1305, 385, 1360, 385, "$batch")

# ---- microsoft 365 -------------------------------------------------------
zone(1360, 105, 420, 560, "MICROSOFT 365 CLOUD", "The tenant side")
rect(1380, 160, 380, 76, NAVY, DEEP, 1.2)
text(1396, 188, "Copilot connectors API", 14, WHITE, "600")
text(1396, 210, "Connections, schema, items, $batch", 10.5, "#B9CBDD")
rect(1380, 256, 380, 84, WHITE, NAVY, 1.2)
text(1396, 282, "Microsoft Entra ID", 13, NAVY, "600")
text(1396, 302, "One AD group per connector expresses", 10, INK)
text(1396, 318, "every item's ACL. No user ACEs.", 10, INK)
text(1396, 334, "Revocation runs through AD.", 10, MUTED)
rect(1380, 372, 380, 72, "#EAF2EA", GREEN, 1.4)
text(1396, 398, "Microsoft Search", 13, "#2F6B33", "600")
text(1396, 420, "Result types and display templates", 10, INK)
rect(1380, 460, 380, 72, "#EAF2EA", GREEN, 1.4)
text(1396, 486, "Microsoft 365 Copilot", 13, "#2F6B33", "600")
text(1396, 508, "Grounded on connector content", 10, INK)
rect(1380, 548, 380, 96, WHITE, RULE, 1.2, dash="5 4")
text(1396, 574, "Never reaches the index", 12, RED, "600")
for j, ln in enumerate(["Row-filtered and masked objects",
                        "Objects the source grants to nobody",
                        "Anything a guard refused"]):
    text(1396, 596 + j * 16, "· " + ln, 10, INK)

# ---- operations ----------------------------------------------------------
zone(40, 690, 1740, 190, "OPERATIONS", "Read only, and out of the write path")
ops = [("Operations dashboard", "Runs, items, health. By group membership"),
       ("Health watchdog", "Freshness, and the paging matrix behind it"),
       ("Reconciliation", "Inventory to index, and source to inventory"),
       ("OTLP collector", "Spans and metrics per run. Optional"),
       ("Release package", "Authenticode, file catalog, SBOM")]
for i, (t, d) in enumerate(ops):
    x = 60 + i * 344
    rect(x, 740, 324, 112, WHITE, NAVY, 1.2)
    text(x + 16, 768, t, 12.5, NAVY, "600")
    text(x + 16, 790, d, 10, INK)
arrow(1090, 664, 1090, 740)

text(40, 930, "What a source concept becomes", 13, NAVY, "600")
rows = [("A group grant on an object", "the connector's single AD group"),
        ("A deny, a row filter, a mask", "a refusal to index, not a narrower ACL"),
        ("A grant to a named individual", "nothing — a Graph ACL carries group ids"),
        ("A time-bounded or conditional grant", "a refusal, or a stated staleness bound")]
for i, (a, b) in enumerate(rows):
    y = 960 + i * 26
    text(60, y, a, 11, INK)
    text(430, y, "→", 11, ORANGE, "600")
    text(470, y, b, 11, MUTED)
text(40, H - 24, "Regenerate with .github/scripts/render-architecture.py — "
                 "see connector-tiers.svg for what adding a connector costs.", 10.5, MUTED, mono=True)
p.append("</svg>")
OUT.write_text("\n".join(p), encoding="utf-8")
print("wrote", OUT, OUT.stat().st_size, "bytes")
