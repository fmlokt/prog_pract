// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: deep-blue; icon-glyph: hourglass-half;

// ============================================================================
// Countdown Lock Screen Widget for Scriptable (iOS 16+)
// ----------------------------------------------------------------------------
// Counts down to an END date. Depending on the widget family it shows either
// the remaining time or the progress travelled from a START date to the END:
//
//   * accessoryRectangular / systemSmall : days + hours remaining to the end.
//   * accessoryInline  (Lock Screen date line) : ASCII progress bar [===.....]
//     of 10 sections, filling as now moves from start -> end.
//   * accessoryCircular : the same progress as a percentage value.
//
// In every case the countdown TARGET is the end date; the start date is used
// only as the 0% reference for the progress bar / percentage.
//
// SETUP
//   1. Open the Scriptable app, create a new script, and paste this file.
//   2. Long-press your Lock Screen -> Customize -> add a Scriptable widget
//      (rectangular, inline, or circular).
//   3. Tap the widget and choose this script.
//   4. In the widget's "Parameter" field, provide the dates and an optional
//      title, separated by "|":
//
//         START | END | TITLE
//
//      Examples:
//         2026-01-01 | 2026-12-31 | The Year
//         2026-09-01 08:00 | 2027-06-15 | School Year
//
//      You may also give just an END date (start defaults to DEFAULT_START):
//         2026-12-31 | New Year
//
// Dates are parsed as LOCAL time. Accepted formats:
//   YYYY-MM-DD
//   YYYY-MM-DD HH:MM
//   YYYY-MM-DDTHH:MM
// ============================================================================

// ----- Defaults (used when no widget parameter is provided) -----------------
const DEFAULT_START = "2026-01-01 00:00"; // 0% reference for the progress bar
const DEFAULT_END = "2026-12-31 00:00"; // countdown target / 100% reference
const DEFAULT_TITLE = "Countdown"; // label shown on the rectangular widget

// ----- Parse configuration --------------------------------------------------
const config = parseParameter(args.widgetParameter);
const start = parseDate(config.start);
const end = parseDate(config.end);
const title = config.title;

// ----- Compute remaining time + progress ------------------------------------
const now = new Date();
const remaining = computeRemaining(now, end);
const progress = computeProgress(now, start, end); // 0..1

// ----- Build the widget -----------------------------------------------------
const family = config.family || "accessoryRectangular";
const widget = createWidget(remaining, progress, title, family);

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  // When run inside the app, preview according to the chosen family.
  if (family === "accessoryInline") widget.presentAccessoryInline();
  else if (family === "accessoryCircular") widget.presentAccessoryCircular();
  else if (family === "systemSmall") widget.presentSmall();
  else widget.presentAccessoryRectangular();
}

Script.complete();

// ============================================================================
// Functions
// ============================================================================

// Parse the widget parameter string into { start, end, title }.
// Supported forms:
//   "START | END | TITLE"
//   "START | END"
//   "END | TITLE"   (single date -> treated as the end date)
//   "END"
function parseParameter(param) {
  const out = {
    start: DEFAULT_START,
    end: DEFAULT_END,
    title: DEFAULT_TITLE,
    family: config_family(),
    runsInWidget: typeof args !== "undefined" && args.runsInWidget,
  };
  if (param && typeof param === "string" && param.trim().length) {
    const parts = param.split("|").map((p) => p.trim());
    const dateCount = parts.filter((p) => looksLikeDate(p)).length;

    if (dateCount >= 2) {
      // START | END | [TITLE]
      out.start = parts[0];
      out.end = parts[1];
      if (parts[2] && parts[2].length) out.title = parts[2];
    } else {
      // END | [TITLE]  (start stays at the default reference)
      if (parts[0] && parts[0].length) out.end = parts[0];
      if (parts[1] && parts[1].length) out.title = parts[1];
    }
  }
  return out;
}

// Rough check whether a field is a date rather than a title.
function looksLikeDate(str) {
  return /^\d{4}-\d{2}-\d{2}/.test(String(str).trim());
}

// Determine which widget family we're running as.
function config_family() {
  if (typeof args !== "undefined" && args.widgetFamily) return args.widgetFamily;
  return null;
}

// Parse a date string (local time) into a Date object.
function parseDate(str) {
  // Normalize "YYYY-MM-DD HH:MM" and "YYYY-MM-DDTHH:MM".
  const m = String(str)
    .trim()
    .match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/);
  if (!m) {
    // Fall back to the native parser for anything unexpected.
    const d = new Date(str);
    if (!isNaN(d.getTime())) return d;
    // Last resort: default end date so the widget never crashes.
    return new Date(DEFAULT_END.replace(" ", "T"));
  }
  const [, y, mo, d, h, mi, s] = m;
  return new Date(
    Number(y),
    Number(mo) - 1,
    Number(d),
    h ? Number(h) : 0,
    mi ? Number(mi) : 0,
    s ? Number(s) : 0
  );
}

// Compute the remaining days/hours between now and the end date.
function computeRemaining(now, end) {
  let diffMs = end.getTime() - now.getTime();
  const past = diffMs < 0;
  diffMs = Math.abs(diffMs);

  const totalHours = Math.floor(diffMs / (1000 * 60 * 60));
  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;

  return { days, hours, past };
}

// Compute progress from start -> end as a fraction in [0, 1].
function computeProgress(now, start, end) {
  const span = end.getTime() - start.getTime();
  if (span <= 0) return 1; // degenerate/invalid span -> treat as complete
  const p = (now.getTime() - start.getTime()) / span;
  return Math.max(0, Math.min(1, p));
}

// Build the Scriptable widget for the given family.
function createWidget(r, progress, title, family) {
  const w = new ListWidget();
  w.backgroundColor = new Color("#000000", 0); // transparent on lock screen

  const accent = new Color("#4DA6FF"); // number color
  const dim = Color.dynamic(new Color("#8E8E93"), new Color("#8E8E93"));

  if (family === "accessoryInline") {
    // Single line rendered by iOS on the Lock Screen date line: ASCII bar.
    w.addText(progressBar(progress, 10));
    return w;
  }

  if (family === "accessoryCircular") {
    // Show the progress as a percentage value only (no label/title).
    const stack = w.addStack();
    stack.layoutVertically();
    stack.centerAlignContent();
    const num = stack.addText(`${Math.round(progress * 100)}%`);
    num.font = Font.boldSystemFont(20);
    num.centerAlignText();
    return w;
  }

  // Default: accessoryRectangular (also used for systemSmall preview).
  const header = w.addText(r.past ? title + " (ago)" : title);
  header.font = Font.mediumSystemFont(12);
  header.textColor = dim;
  header.lineLimit = 1;

  w.addSpacer(3);

  const row = w.addStack();
  row.centerAlignContent();

  addUnit(row, r.days, r.days === 1 ? "day" : "days", accent);
  row.addSpacer(8);
  addUnit(row, r.hours, r.hours === 1 ? "hr" : "hrs", accent);

  return w;
}

// Add a big number + small unit label to a stack.
function addUnit(stack, value, label, accent) {
  const s = stack.addStack();
  s.layoutVertically();

  const num = s.addText(String(value));
  num.font = Font.boldSystemFont(22);
  num.textColor = accent;
  num.leftAlignText();

  const lbl = s.addText(label);
  lbl.font = Font.systemFont(10);
  lbl.textColor = new Color("#8E8E93");
  lbl.leftAlignText();
}

// Render a fixed-width ASCII progress bar, e.g. "[===.......]" for 10 sections.
function progressBar(progress, sections) {
  const filled = Math.round(progress * sections);
  const empty = sections - filled;
  return "[" + "=".repeat(filled) + ".".repeat(empty) + "]";
}
