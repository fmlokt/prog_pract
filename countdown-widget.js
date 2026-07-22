// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: deep-blue; icon-glyph: hourglass-half;

// ============================================================================
// Countdown Lock Screen Widget for Scriptable (iOS 16+)
// ----------------------------------------------------------------------------
// Shows the number of days and hours remaining until a target date.
// Designed primarily for the LOCK SCREEN accessory widgets, but also renders
// on the Home Screen (small family).
//
// SETUP
//   1. Open the Scriptable app and create a new script, paste this file.
//   2. Long-press your Lock Screen -> Customize -> add a Scriptable widget
//      (rectangular is recommended, inline & circular are also supported).
//   3. Tap the widget and choose this script.
//   4. In the widget's "Parameter" field, set your target date and an
//      optional title, separated by a "|". Examples:
//         2026-12-31 23:59 | New Year
//         2026-09-01 | First Day of School
//         2026-08-15
//      If no parameter is given, the DEFAULT_* values below are used.
//
// The date is parsed as local time. Accepted formats:
//   YYYY-MM-DD
//   YYYY-MM-DD HH:MM
//   YYYY-MM-DDTHH:MM
// ============================================================================

// ----- Defaults (used when no widget parameter is provided) -----------------
const DEFAULT_DATE = "2026-12-31 00:00"; // target date/time (local)
const DEFAULT_TITLE = "Countdown"; // label shown above the numbers

// ----- Parse configuration --------------------------------------------------
const config = parseParameter(args.widgetParameter);
const target = parseDate(config.date);
const title = config.title;

// ----- Compute remaining time ----------------------------------------------
const now = new Date();
const remaining = computeRemaining(now, target);

// ----- Build the widget -----------------------------------------------------
const family = config.family || "accessoryRectangular";
const widget = createWidget(remaining, title, family);

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

// Parse the widget parameter string into { date, title }.
function parseParameter(param) {
  const out = {
    date: DEFAULT_DATE,
    title: DEFAULT_TITLE,
    family: config_family(),
    runsInWidget: typeof args !== "undefined" && args.runsInWidget,
  };
  if (param && typeof param === "string" && param.trim().length) {
    const parts = param.split("|");
    if (parts[0] && parts[0].trim().length) out.date = parts[0].trim();
    if (parts[1] && parts[1].trim().length) out.title = parts[1].trim();
  }
  return out;
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
    // Last resort: default date so the widget never crashes.
    return new Date(DEFAULT_DATE.replace(" ", "T"));
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

// Compute the remaining days/hours between now and target.
function computeRemaining(now, target) {
  let diffMs = target.getTime() - now.getTime();
  const past = diffMs < 0;
  diffMs = Math.abs(diffMs);

  const totalHours = Math.floor(diffMs / (1000 * 60 * 60));
  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;

  return { days, hours, past, target };
}

// Build the Scriptable widget for the given family.
function createWidget(r, title, family) {
  const w = new ListWidget();
  w.backgroundColor = new Color("#000000", 0); // transparent on lock screen

  const accent = new Color("#4DA6FF"); // number color
  const dim = Color.dynamic(new Color("#8E8E93"), new Color("#8E8E93"));

  if (family === "accessoryInline") {
    // Single line of text, rendered by iOS next to the clock.
    w.addText(inlineText(r, title));
    return w;
  }

  if (family === "accessoryCircular") {
    const stack = w.addStack();
    stack.layoutVertically();
    stack.centerAlignContent();
    const num = stack.addText(String(r.days));
    num.font = Font.boldSystemFont(20);
    num.centerAlignText();
    const lbl = stack.addText("days");
    lbl.font = Font.systemFont(9);
    lbl.centerAlignText();
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

// Build the one-line string for the inline accessory family (the slot on the
// Lock Screen's date line). Space is very tight here, so output just the days
// and hours. A short title is prefixed only if one was provided; the built-in
// default title is omitted to keep it compact.
function inlineText(r, title) {
  const core = `${r.days}d ${r.hours}h`;
  const hasCustomTitle = title && title !== DEFAULT_TITLE;
  const prefix = hasCustomTitle ? `${title}: ` : "";
  return `${prefix}${core}`;
}
