"""Populate the supplied UniHack template with an editable project presentation.

Run with the system Python while LibreOffice listens on port 2002:
    /usr/bin/python3 scripts/build_unihack_deck.py
"""

from pathlib import Path
import subprocess
import time
import uno
from com.sun.star.awt import Point, Size
from com.sun.star.beans import PropertyValue


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "[EXT] UniHack-Protoype Template  (1).pptx"
OUTPUT = ROOT / "Error_404_UniHack_Product_Intelligence.pptx"

# The supplied template uses a 10 × 5.625 in canvas.  Layout coordinates below
# were drafted on a 13.33 × 7.5 grid, so helpers scale them to the template.
DESIGN_W, DESIGN_H = 33867, 19050
W, H = 25400, 14288
SX, SY = W / DESIGN_W, H / DESIGN_H

NAVY = 0x08131F
PANEL = 0x102235
PANEL_2 = 0x152B40
CYAN = 0x37D9D0
TEAL = 0x16A085
GREEN = 0x20BF78
AMBER = 0xF4B942
RED = 0xE76F51
WHITE = 0xF4F7FA
MUTED = 0xA7B8C8
LINE = 0x2C4B63


def prop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def rect(doc, page, x, y, w, h, color, radius=False, line=LINE):
    shape = doc.createInstance("com.sun.star.drawing.RectangleShape")
    shape.Position = Point(int(x * SX), int(y * SY))
    shape.Size = Size(int(w * SX), int(h * SY))
    shape.FillColor = color
    shape.LineColor = line
    shape.LineWidth = int(25 * SX)
    if radius:
        try:
            shape.CornerRadius = 300
        except Exception:
            pass
    page.add(shape)
    return shape


def text(doc, page, value, x, y, w, h, size=18, color=WHITE, bold=False, align=0):
    shape = doc.createInstance("com.sun.star.drawing.TextShape")
    shape.Position = Point(int(x * SX), int(y * SY))
    shape.Size = Size(int(w * SX), int(h * SY))
    # LibreOffice applies text properties reliably only after the shape is
    # attached to a draw page.
    page.add(shape)
    shape.String = value
    shape.CharColor = color
    shape.CharHeight = size * SX
    shape.CharFontName = "Liberation Sans"
    shape.CharWeight = 150 if bold else 100
    shape.ParaAdjust = align
    shape.TextWordWrap = True
    return shape


def bullet_list(doc, page, items, x, y, w, start=19, gap=980):
    for idx, item in enumerate(items):
        text(doc, page, "•", x, y + idx * gap, 450, 500, start, CYAN, True)
        text(doc, page, item, x + 520, y + idx * gap, w - 520, 700, start, WHITE)


def chip(doc, page, label, x, y, w, color=CYAN):
    rect(doc, page, x, y, w, 600, PANEL_2, True, color)
    text(doc, page, label, x + 120, y + 130, w - 240, 330, 12, color, True, 1)


def title(doc, page, kicker, heading, sub=""):
    text(doc, page, kicker.upper(), 1650, 920, 14000, 450, 12, CYAN, True)
    text(doc, page, heading, 1650, 1400, 30000, 2100, 30, WHITE, True)
    if sub:
        text(doc, page, sub, 1650, 3600, 29200, 700, 15, MUTED)
    rect(doc, page, 1650, 4350, 30550, 28, CYAN, False, CYAN)


def footer(doc, page, number):
    text(doc, page, "ERROR 404  |  UNI HACK 2026", 1650, 17930, 11000, 360, 10, MUTED, True)
    text(doc, page, f"{number:02d}", 30550, 17930, 1600, 360, 10, MUTED, True, 2)


def flow_box(doc, page, label, detail, x, y, w=4700, accent=CYAN):
    rect(doc, page, x, y, w, 3300, PANEL, True, accent)
    text(doc, page, label, x + 280, y + 280, w - 560, 1050, 17, accent, True, 1)
    text(doc, page, detail, x + 280, y + 1600, w - 560, 1450, 13, WHITE, False, 1)


def arrow(doc, page, x, y):
    text(doc, page, "→", x, y, 800, 700, 25, CYAN, True, 1)


def placeholder(doc, page, label, x, y, w, h):
    rect(doc, page, x, y, w, h, PANEL, True, LINE)
    text(doc, page, "IMAGE / SCREENSHOT PLACEHOLDER", x + 400, y + h // 2 - 380, w - 800, 340, 11, MUTED, True, 1)
    text(doc, page, label, x + 400, y + h // 2 + 70, w - 800, 580, 15, CYAN, True, 1)


def clear_page(page):
    while page.getCount():
        page.remove(page.getByIndex(0))


def background(doc, page):
    rect(doc, page, 0, 0, DESIGN_W, DESIGN_H, NAVY, False, NAVY)
    rect(doc, page, 0, 0, 420, DESIGN_H, CYAN, False, CYAN)


def build(doc):
    pages = doc.getDrawPages()
    while pages.getCount() < 15:
        pages.insertNewByIndex(pages.getCount())
    for i in range(pages.getCount()):
        clear_page(pages.getByIndex(i))

    # 1. Cover
    p = pages.getByIndex(0); background(doc, p)
    text(doc, p, "UNI HACK 2026", 1800, 1300, 9000, 500, 15, CYAN, True)
    text(doc, p, "Evidence-First\nProduct Intelligence", 1800, 2250, 19000, 2600, 39, WHITE, True)
    text(doc, p, "Turning fragmented industrial product data into structured, traceable, commerce-ready intelligence.", 1800, 5500, 17700, 1500, 18, MUTED)
    chip(doc, p, "AI-POWERED PRODUCT INTELLIGENCE", 1800, 7900, 10000)
    rect(doc, p, 22000, 2100, 8400, 9400, PANEL, True, CYAN)
    text(doc, p, "SUPPLIER DATA", 22900, 3100, 6600, 450, 16, CYAN, True, 1)
    text(doc, p, "→", 24700, 3900, 3000, 900, 36, WHITE, True, 1)
    text(doc, p, "VERIFIED\nPRODUCT RECORD", 22900, 5300, 6600, 1100, 22, GREEN, True, 1)
    text(doc, p, "Official evidence • Gemini extraction • Human validation", 22900, 8200, 6600, 800, 14, MUTED, False, 1)
    text(doc, p, "Team Error 404", 1800, 15780, 10000, 450, 18, WHITE, True)
    text(doc, p, "Abhishek Vishwakarma", 1800, 16400, 11000, 420, 15, CYAN)
    footer(doc, p, 1)

    # 2. Opportunity
    p = pages.getByIndex(1); background(doc, p); title(doc, p, "The opportunity", "Industrial data is abundant.\nTrustworthy product intelligence is not.")
    flow_box(doc, p, "INPUT", "Supplier spreadsheets\nLimited descriptions\nInconsistent brands", 1800, 4700, 6600, AMBER)
    flow_box(doc, p, "FRICTION", "Manual research\nUnverified attributes\nSlow catalog onboarding", 9750, 4700, 6600, RED)
    flow_box(doc, p, "IMPACT", "Poor discovery\nIncorrect orders\nDelayed commerce readiness", 17700, 4700, 6600, AMBER)
    text(doc, p, "The challenge is not generating text. It is generating reliable product intelligence with proof.", 1800, 8300, 27700, 700, 20, WHITE, True)
    footer(doc, p, 2)

    # 3. Problem
    p = pages.getByIndex(2); background(doc, p); title(doc, p, "Problem statement", "From six raw fields to a 252-column delivery standard")
    rect(doc, p, 1800, 4450, 13000, 8500, PANEL, True, LINE)
    text(doc, p, "RAW SUPPLIER INPUT", 2400, 5100, 9000, 500, 16, AMBER, True)
    bullet_list(doc, p, ["Part number and free-text description", "Conflicting distributor/ERP brand labels", "Sparse or missing technical specifications", "No field-level proof for commerce output"], 2400, 6050, 10500, 17)
    rect(doc, p, 18150, 4450, 13000, 8500, PANEL, True, LINE)
    text(doc, p, "REQUIRED DELIVERY", 18750, 5100, 9000, 500, 16, GREEN, True)
    bullet_list(doc, p, ["Canonical identity and taxonomy", "Controlled LOV attributes and normalized UOM", "Five content tiers and digital assets", "252-column, traceable PIM entity"], 18750, 6050, 10500, 17)
    text(doc, p, "Our answer: do not fill every blank. Fill only what evidence can defend.", 1800, 14400, 28000, 700, 21, CYAN, True)
    footer(doc, p, 3)

    # 4. Solution
    p = pages.getByIndex(3); background(doc, p); title(doc, p, "Our solution", "UniHack Simplifi: evidence-first enrichment with human control", "An operational workbench, not a black-box content generator.")
    cards = [("1", "INGEST", "Raw supplier CSV and product identifiers", AMBER), ("2", "GROUND", "Official manufacturer pages and spec sheets", CYAN), ("3", "EXTRACT", "Gemini structured extraction from source chunks", TEAL), ("4", "VALIDATE", "LOV, UOM, citation and conflict gates", GREEN), ("5", "REVIEW", "Human field-level approval and audit trail", AMBER)]
    for i, (num, label, desc, color) in enumerate(cards):
        x = 1700 + i * 6200
        rect(doc, p, x, 4950, 5200, 4100, PANEL, True, color)
        text(doc, p, num, x + 350, 5350, 900, 700, 27, color, True)
        text(doc, p, label, x + 350, 6300, 4400, 440, 17, WHITE, True)
        text(doc, p, desc, x + 350, 7100, 4400, 900, 14, MUTED)
    footer(doc, p, 4)

    # 5. Workflow
    p = pages.getByIndex(4); background(doc, p); title(doc, p, "End-to-end workflow", "Every published value follows a visible chain of trust")
    labels = [("Supplier Input", "MPN + raw description", AMBER), ("Official Evidence", "URL / PDF + checksum", CYAN), ("Gemini Extract", "Structured candidates", TEAL), ("Deterministic Gates", "Citation + LOV + UOM", GREEN), ("Human Review", "Resolve high-risk fields", AMBER), ("Validated Output", "252-column export", GREEN)]
    for i, (label, desc, color) in enumerate(labels):
        x = 1350 + (i % 3) * 10500
        y = 4900 if i < 3 else 9200
        flow_box(doc, p, label, desc, x, y, 7600, color)
    arrow(doc, p, 9200, 5600); arrow(doc, p, 19700, 5600)
    arrow(doc, p, 9200, 9900); arrow(doc, p, 19700, 9900)
    text(doc, p, "If evidence is insufficient, the product remains Unknown / Needs Review — never silently invented.", 1800, 14550, 28000, 500, 17, WHITE, True, 1)
    footer(doc, p, 5)

    # 6. Architecture
    p = pages.getByIndex(5); background(doc, p); title(doc, p, "System architecture", "A modular backend built for provenance, governance, and scale")
    flow_box(doc, p, "INTERFACE", "React review workbench\nCatalog • evidence • review • export", 1650, 4900, 7700, CYAN)
    flow_box(doc, p, "APPLICATION API", "FastAPI\nRBAC • CSRF • health • API contracts", 13000, 4900, 7700, TEAL)
    flow_box(doc, p, "INTELLIGENCE", "Evidence registry\nGemini provider\nLOV/UOM validation", 24350, 4900, 7700, GREEN)
    arrow(doc, p, 9720, 5550); arrow(doc, p, 21080, 5550)
    flow_box(doc, p, "PERSISTENCE", "SQLite records\nAudit trail • jobs • cache • exports", 7200, 10300, 7700, AMBER)
    flow_box(doc, p, "DELIVERY", "252-column CSV/XLSX\nChecksum + export history", 19000, 10300, 7700, CYAN)
    footer(doc, p, 6)

    # 7. Gemini
    p = pages.getByIndex(6); background(doc, p); title(doc, p, "Gemini’s role", "Gemini extracts candidates. Deterministic gates decide what is trusted.")
    rect(doc, p, 1800, 4650, 13600, 9400, PANEL, True, TEAL)
    text(doc, p, "GEMINI IS CONSTRAINED TO", 2400, 5300, 10000, 500, 16, CYAN, True)
    bullet_list(doc, p, ["Registered official source chunks only", "Structured schema response", "Exact citation excerpt per fact", "Temperature 0 extraction", "Cache keyed by source/model/schema/LOV"], 2400, 6250, 10800, 16)
    rect(doc, p, 17400, 4650, 13600, 9400, PANEL, True, RED)
    text(doc, p, "THE SYSTEM REJECTS", 18000, 5300, 10000, 500, 16, RED, True)
    bullet_list(doc, p, ["Missing or mismatched evidence chunks", "Quoted value absent from source text", "MPN mismatch", "Unsupported LOV/UOM values", "Conflicting or insufficient evidence"], 18000, 6250, 10800, 16)
    footer(doc, p, 7)

    # 8. Evidence
    p = pages.getByIndex(7); background(doc, p); title(doc, p, "Evidence & provenance", "A field is not just a value — it is a value with a source, excerpt, and status")
    rect(doc, p, 1800, 4650, 30300, 8800, PANEL, True, CYAN)
    text(doc, p, "FIELD: Pressure Rating", 2500, 5350, 9000, 480, 18, WHITE, True)
    chip(doc, p, "VERIFIED", 24500, 5220, 4300, GREEN)
    text(doc, p, "Candidate value", 2500, 6400, 6500, 360, 13, MUTED)
    text(doc, p, "200 psi", 2500, 6900, 6500, 520, 23, CYAN, True)
    text(doc, p, "Evidence excerpt", 2500, 8000, 6500, 360, 13, MUTED)
    text(doc, p, "“Maximum working pressure: 200 psi”", 2500, 8500, 19000, 600, 18, WHITE, True)
    text(doc, p, "Source", 2500, 9880, 6500, 360, 13, MUTED)
    text(doc, p, "Official manufacturer specification sheet  •  page 2  •  SHA-256 recorded", 2500, 10380, 25500, 500, 15, WHITE)
    text(doc, p, "This gives reviewers a fast way to approve, edit, reject, or mark a fact unknown.", 2500, 11900, 25500, 520, 16, CYAN, True)
    footer(doc, p, 8)

    # 9. Human review
    p = pages.getByIndex(8); background(doc, p); title(doc, p, "Human-in-the-loop quality gate", "Automation accelerates the work. Specialists retain release authority.")
    for i, (label, desc, color) in enumerate([( "High-risk fields", "MPN • brand • manufacturer • taxonomy • invoice description", RED), ("Reviewer actions", "Approve • edit • reject • mark unknown", AMBER), ("Promotion rule", "Validated only after every high-risk field is resolved", GREEN)]):
        flow_box(doc, p, label, desc, 1800 + i * 10400, 5250, 8400, color)
    text(doc, p, "Every action records reviewer, timestamp, prior value, new value, justification, and audit event.", 1800, 10400, 30000, 560, 18, WHITE, True, 1)
    placeholder(doc, p, "Insert Review Queue screenshot", 8600, 11700, 16600, 3200)
    footer(doc, p, 9)

    # 10. Product experience
    p = pages.getByIndex(9); background(doc, p); title(doc, p, "Product experience", "A focused workbench for catalog specialists")
    placeholder(doc, p, "Insert Transformation Inspector screenshot", 1750, 4400, 14300, 8600)
    placeholder(doc, p, "Insert Evidence Inbox screenshot", 17800, 4400, 14300, 8600)
    text(doc, p, "Catalog Explorer", 2500, 13750, 4800, 400, 15, CYAN, True)
    text(doc, p, "Transformation Inspector", 10000, 13750, 6000, 400, 15, CYAN, True)
    text(doc, p, "Evidence Inbox", 23000, 13750, 4400, 400, 15, CYAN, True)
    footer(doc, p, 10)

    # 11. Output
    p = pages.getByIndex(10); background(doc, p); title(doc, p, "Commerce-ready delivery", "From sparse input to a governed 252-column PIM deliverable")
    flow_box(doc, p, "IDENTITY", "Brand • manufacturer\nMPN • SKU • taxonomy", 1700, 4800, 7100, CYAN)
    flow_box(doc, p, "CONTENT", "Invoice • mobile\nshort • long descriptions", 9350, 4800, 7100, TEAL)
    flow_box(doc, p, "SPECIFICATIONS", "LOV attributes\nNormalized UOM • dimensions", 17000, 4800, 7100, GREEN)
    flow_box(doc, p, "DELIVERY", "CSV/XLSX export\nChecksum • history • audit", 24650, 4800, 7100, AMBER)
    text(doc, p, "Values without sufficient evidence remain blank or explicitly marked for review — protecting downstream commerce systems.", 2000, 10150, 29500, 700, 18, WHITE, True, 1)
    footer(doc, p, 11)

    # 12. Security
    p = pages.getByIndex(11); background(doc, p); title(doc, p, "Trust & security by design", "Industrial data quality requires both model governance and application security")
    bullets = [("Secure access", "Role-based access, HttpOnly session cookies, CSRF checks, token revocation", CYAN), ("Evidence safety", "Manufacturer allowlist, SSRF protection, size/type checks, checksums", GREEN), ("Release controls", "High-risk field gate, audit logs, export checksums, source lifecycle", AMBER), ("Honest AI", "Candidate ≠ verified, deterministic citation validation, human review", TEAL)]
    for i, (h, d, c) in enumerate(bullets):
        x = 1800 + (i % 2) * 15700; y = 4650 + (i // 2) * 4400
        rect(doc, p, x, y, 13900, 3300, PANEL, True, c)
        text(doc, p, h, x + 550, y + 500, 12000, 450, 19, c, True)
        text(doc, p, d, x + 550, y + 1300, 12000, 900, 15, WHITE)
    footer(doc, p, 12)

    # 13. Evaluation
    p = pages.getByIndex(12); background(doc, p); title(doc, p, "Truthful evaluation", "We separate structural compliance from ground-truth accuracy")
    rect(doc, p, 1800, 4750, 14200, 8200, PANEL, True, CYAN)
    text(doc, p, "ALWAYS MEASURABLE", 2500, 5400, 10000, 470, 16, CYAN, True)
    bullet_list(doc, p, ["252-column schema conformance", "Invoice and mobile description hard gates", "LOV/UOM validation", "Evidence coverage and unresolved fields"], 2500, 6400, 10500, 17)
    rect(doc, p, 17800, 4750, 14200, 8200, PANEL, True, AMBER)
    text(doc, p, "ONLY WITH LABELLED MATCHES", 18500, 5400, 11200, 470, 16, AMBER, True)
    bullet_list(doc, p, ["Exact-match accuracy", "Description similarity", "Attribute precision / recall / F1", "No match → N/A, never a fabricated 100%"], 18500, 6400, 10500, 17)
    footer(doc, p, 13)

    # 14. Scale
    p = pages.getByIndex(13); background(doc, p); title(doc, p, "Path to scale", "Designed as a foundation for enterprise catalog operations")
    roadmap = [("NOW", "1000-SKU prototype\nEvidence-first workflow\nGemini + HITL", CYAN), ("NEXT", "Persistent job orchestration\nSource lifecycle\nExport history", TEAL), ("ENTERPRISE", "Distributed workers\nVector retrieval\nMulti-tenant governance", GREEN)]
    for i, (phase, body, color) in enumerate(roadmap):
        x = 2200 + i * 10200
        rect(doc, p, x, 5300, 8300, 5700, PANEL, True, color)
        text(doc, p, phase, x + 550, 5900, 7000, 500, 18, color, True, 1)
        text(doc, p, body, x + 700, 6900, 6900, 2600, 16, WHITE, True, 1)
        if i < 2: arrow(doc, p, x + 8500, 7200)
    text(doc, p, "The principle remains the same at every scale: evidence before automation, and humans before irreversible release.", 2100, 12800, 29500, 600, 17, MUTED, False, 1)
    footer(doc, p, 14)

    # 15. Close
    p = pages.getByIndex(14); background(doc, p)
    text(doc, p, "ERROR 404", 1800, 1900, 10000, 500, 15, CYAN, True)
    text(doc, p, "Build commerce-ready\nproduct intelligence\nthat can explain itself.", 1800, 2900, 19600, 2500, 36, WHITE, True)
    rect(doc, p, 21800, 3150, 8700, 6700, PANEL, True, CYAN)
    text(doc, p, "DEMO FLOW", 22900, 4050, 6500, 450, 17, CYAN, True, 1)
    text(doc, p, "1. Inspect raw input\n2. Register official evidence\n3. Extract & validate\n4. Review high-risk fields\n5. Promote & export", 22900, 5050, 6500, 2700, 17, WHITE, False, 1)
    text(doc, p, "Thank you", 1800, 14350, 8500, 600, 25, CYAN, True)
    text(doc, p, "Abhishek Vishwakarma  |  Team Error 404", 1800, 15350, 16000, 430, 16, WHITE)
    footer(doc, p, 15)


def main():
    # Keep the office listener and UNO client in the same process tree. This is
    # more reliable than relying on a detached headless LibreOffice process.
    profile = "file:///tmp/unihack-lo-profile"
    Path("/tmp/unihack-lo-profile").mkdir(parents=True, exist_ok=True)
    office = subprocess.Popen(
        [
            "soffice", "--headless", f"-env:UserInstallation={profile}",
            "--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext",
            "--norestore", "--nofirststartwizard",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx
    )
    ctx = None
    for _ in range(30):
        try:
            ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
            break
        except Exception:
            time.sleep(0.25)
    if ctx is None:
        office.terminate()
        raise RuntimeError("LibreOffice automation listener did not start")
    desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(SOURCE)), "_blank", 0, ())
    build(doc)
    doc.storeAsURL(uno.systemPathToFileUrl(str(OUTPUT)), (prop("FilterName", "Impress MS PowerPoint 2007 XML"),))
    doc.close(True)
    office.terminate()
    print(OUTPUT)


if __name__ == "__main__":
    main()
