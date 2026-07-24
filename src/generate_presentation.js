const pptxgen = require("pptxgenjs");
const path = require("path");

const FIG = (name) => path.join(__dirname, "..", "reports", "figures", name);

// ---- Design tokens (matches dashboard: field-green + harvest-gold agricultural theme) ----
const PRIMARY = "1B4332";      // deep forest green
const PRIMARY_LIGHT = "2D6A4F";
const ACCENT = "E9C46A";       // harvest gold
const ACCENT2 = "588157";      // sage green
const SOIL = "7F5539";         // soil brown
const INK = "1B1B18";
const MUTED = "6B7061";
const CARD = "FFFFFF";
const BG = "F7F5EF";
const LOW = "BC6C25";

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5 in
pres.author = "ML Capstone";
pres.title = "Agricultural Crop-Yield Prediction";

const FONT_HEAD = "Georgia";
const FONT_BODY = "Calibri";

function bgSlide(bg = BG) {
  let s = pres.addSlide();
  s.background = { color: bg };
  return s;
}

function eyebrow(s, text, opts = {}) {
  s.addText(text.toUpperCase(), {
    x: opts.x ?? 0.6, y: opts.y ?? 0.42, w: opts.w ?? 8, h: 0.35,
    fontFace: FONT_BODY, fontSize: 12, color: opts.color ?? ACCENT2,
    bold: true, charSpacing: 2,
  });
}

function title(s, text, opts = {}) {
  s.addText(text, {
    x: opts.x ?? 0.6, y: opts.y ?? 0.72, w: opts.w ?? 12.1, h: opts.h ?? 0.9,
    fontFace: FONT_HEAD, fontSize: opts.size ?? 32, color: opts.color ?? PRIMARY,
    bold: true,
  });
}

function pageNum(s, n) {
  s.addText(String(n).padStart(2, "0"), {
    x: 12.6, y: 7.05, w: 0.6, h: 0.3, fontFace: FONT_BODY, fontSize: 10, color: MUTED, align: "right",
  });
}

// =========================================================== SLIDE 1 — TITLE
{
  let s = bgSlide(PRIMARY);
  s.addShape(pres.ShapeType.ellipse, { x: 10.6, y: -1.6, w: 4.6, h: 4.6, fill: { color: PRIMARY_LIGHT, transparency: 30 }, line: { type: "none" } });
  s.addShape(pres.ShapeType.ellipse, { x: -1.4, y: 5.4, w: 3.6, h: 3.6, fill: { color: ACCENT, transparency: 85 }, line: { type: "none" } });

  s.addText("MACHINE LEARNING CAPSTONE  ·  REGRESSION", {
    x: 0.9, y: 2.15, w: 10, h: 0.4, fontFace: FONT_BODY, fontSize: 13, color: ACCENT, bold: true, charSpacing: 2,
  });
  s.addText("Crop Yield Intelligence", {
    x: 0.85, y: 2.55, w: 11.5, h: 1.3, fontFace: FONT_HEAD, fontSize: 48, color: "FFFFFF", bold: true,
  });
  s.addText("Predicting district-level crop yield across India to spot high- and low-productivity\ndistricts before the season's outcome is known.", {
    x: 0.9, y: 3.75, w: 9.5, h: 0.9, fontFace: FONT_BODY, fontSize: 16, color: "E7E5DA", lineSpacingMultiple: 1.25,
  });

  const stats = [["7", "States"], ["112", "Districts"], ["80", "Crops"], ["49,170", "Records"]];
  let sx = 0.9;
  stats.forEach(([num, label]) => {
    s.addText(num, { x: sx, y: 5.0, w: 2.1, h: 0.6, fontFace: FONT_HEAD, fontSize: 30, color: ACCENT, bold: true });
    s.addText(label.toUpperCase(), { x: sx, y: 5.62, w: 2.1, h: 0.35, fontFace: FONT_BODY, fontSize: 10.5, color: "C8C4B4", charSpacing: 1.5 });
    sx += 2.15;
  });

  s.addText("1997 – 2014  ·  Government of India Open Data Platform", {
    x: 0.9, y: 6.85, w: 8, h: 0.35, fontFace: FONT_BODY, fontSize: 11, color: "9CA595", italic: true,
  });
}

// =========================================================== SLIDE 2 — BUSINESS PROBLEM
{
  let s = bgSlide();
  eyebrow(s, "01 · Business Problem");
  title(s, "Yield varies district by district —\nplanners find out only after the season");

  const cards = [
    { h: "Target Users", b: "Agriculture departments, crop insurers, agri-input companies, and farmer-advisory services." },
    { h: "The Gap", b: "Crop yield varies widely by district, crop, and season — with no early warning before harvest." },
    { h: "The Outcome", b: "A district × crop × season yield estimate that flags likely under-performers early." },
    { h: "The Value", b: "Better-targeted subsidies and evidence-based planning — business value and social value together." },
  ];
  let cx = 0.6, cy = 2.15, cw = 2.95, ch = 3.6, gap = 0.28;
  cards.forEach((c, i) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: cx, y: cy, w: cw, h: ch, rectRadius: 0.12,
      fill: { color: CARD }, line: { color: "E5E2D8", width: 1 },
      shadow: { type: "outer", color: "1B4332", opacity: 0.12, blur: 6, offset: 2, angle: 90 },
    });
    s.addText(c.h, { x: cx + 0.22, y: cy + 0.28, w: cw - 0.44, h: 0.5, fontFace: FONT_HEAD, fontSize: 16, color: PRIMARY, bold: true });
    s.addText(c.b, { x: cx + 0.22, y: cy + 0.85, w: cw - 0.44, h: ch - 1.1, fontFace: FONT_BODY, fontSize: 12, color: INK, lineSpacingMultiple: 1.25 });
    cx += cw + gap;
  });
  pageNum(s, 2);
}

// =========================================================== SLIDE 3 — DATASET & CONSTRAINT
{
  let s = bgSlide();
  eyebrow(s, "02 · Data Collection");
  title(s, "One dataset, one hard rule");

  s.addText("Source", { x: 0.6, y: 2.1, w: 6, h: 0.4, fontFace: FONT_BODY, fontSize: 13, color: SOIL, bold: true });
  s.addText("District-wise, Season-wise Crop Production Statistics\nGovernment of India Open Data Platform", {
    x: 0.6, y: 2.5, w: 6.4, h: 0.9, fontFace: FONT_BODY, fontSize: 15, color: INK, lineSpacingMultiple: 1.3,
  });

  s.addText("Scale", { x: 0.6, y: 3.55, w: 6, h: 0.4, fontFace: FONT_BODY, fontSize: 13, color: SOIL, bold: true });
  const rows = ["49,784 raw records  →  49,170 after cleaning", "1997 – 2014  ·  7 states  ·  112 districts  ·  80 crops",
                "Zero missing values, zero duplicates — 109 zero-production rows removed"];
  s.addText(rows.map(r => ({ text: r, options: { bullet: { code: "25CF" }, breakLine: true, color: INK, fontSize: 13 } })), {
    x: 0.6, y: 3.95, w: 6.4, h: 1.6, fontFace: FONT_BODY, lineSpacingMultiple: 1.35,
  });

  // Signature callout card
  s.addShape(pres.ShapeType.roundRect, {
    x: 7.4, y: 2.1, w: 5.35, h: 4.4, rectRadius: 0.14, fill: { color: PRIMARY }, line: { type: "none" },
  });
  s.addText("THE ONE RULE", { x: 7.75, y: 2.45, w: 4.6, h: 0.35, fontFace: FONT_BODY, fontSize: 12, color: ACCENT, bold: true, charSpacing: 2 });
  s.addText("Yield = Production ÷ Area", { x: 7.75, y: 2.85, w: 4.6, h: 0.6, fontFace: FONT_HEAD, fontSize: 22, color: "FFFFFF", bold: true });
  s.addText("Production is the target's own ingredient — so Production is never fed to the model as an input. Using it would leak the answer directly into the features.", {
    x: 7.75, y: 3.55, w: 4.6, h: 1.6, fontFace: FONT_BODY, fontSize: 13.5, color: "E7E5DA", lineSpacingMultiple: 1.35,
  });
  s.addText("Features used instead: State, District, Crop, Season, Year, Cultivated Area, and engineered historical-yield features.", {
    x: 7.75, y: 5.25, w: 4.6, h: 1.1, fontFace: FONT_BODY, fontSize: 12, color: "C8C4B4", italic: true, lineSpacingMultiple: 1.3,
  });
  pageNum(s, 3);
}

// =========================================================== SLIDE 4 — PREPROCESSING
{
  let s = bgSlide();
  eyebrow(s, "03 · Data Quality & Preprocessing");
  title(s, "Cleaning decisions, each with a reason");

  const steps = [
    ["Type correction", "Year → int; categorical fields trimmed & cast to string"],
    ["Invalid records dropped", "Area ≤ 0 or Production < 0 removed (109 rows)"],
    ["Target recomputed", "Yield = Production ÷ Area, calculated fresh — not trusted from source"],
    ["Per-crop outlier capping", "±3×IQR computed separately per crop — yield scale differs hugely by crop type"],
    ["Leakage columns dropped", "Production and the source Yield column excluded entirely"],
  ];
  let y = 2.15;
  steps.forEach(([h, b], i) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: 0.6, y, w: 12.1, h: 0.82, rectRadius: 0.08, fill: { color: CARD }, line: { color: "E5E2D8", width: 1 },
    });
    s.addText(h, { x: 0.9, y: y + 0.08, w: 3.6, h: 0.66, fontFace: FONT_HEAD, fontSize: 14, color: PRIMARY, bold: true, valign: "middle" });
    s.addText(b, { x: 4.6, y: y + 0.08, w: 7.9, h: 0.66, fontFace: FONT_BODY, fontSize: 12.5, color: INK, valign: "middle" });
    y += 0.95;
  });
  s.addText("Net effect: 1.23% of rows removed, all justified above", {
    x: 0.6, y: y + 0.05, w: 8, h: 0.35, fontFace: FONT_BODY, fontSize: 12, color: MUTED, italic: true,
  });
  pageNum(s, 4);
}

// =========================================================== SLIDE 5 — EDA (images)
{
  let s = bgSlide();
  eyebrow(s, "04 · Exploratory Data Analysis");
  title(s, "Past performance beats field size");

  s.addImage({ path: FIG("03_correlation_heatmap.png"), x: 0.6, y: 2.05, w: 5.5, h: 4.6 });
  s.addImage({ path: FIG("06_avg_yield_by_state.png"), x: 6.4, y: 2.05, w: 6.3, h: 3.05 });

  s.addShape(pres.ShapeType.roundRect, {
    x: 6.4, y: 5.25, w: 6.3, h: 1.4, rectRadius: 0.1, fill: { color: BG }, line: { color: "E5E2D8", width: 1 },
  });
  s.addText("Historical_Yield correlates with the target at r ≈ 0.90 — while raw cultivated Area barely correlates at all. Past performance, not scale, drives yield.", {
    x: 6.65, y: 5.4, w: 6.0, h: 1.1, fontFace: FONT_BODY, fontSize: 13, color: INK, lineSpacingMultiple: 1.3,
  });
  pageNum(s, 5);
}

// =========================================================== SLIDE 6 — FEATURE ENGINEERING
{
  let s = bgSlide();
  eyebrow(s, "05 · Feature Engineering");
  title(s, "Built from the past, safely");

  const feats = [
    ["Historical_Yield", "Lag-1 yield for the same State + District + Crop + Season"],
    ["Historical_Yield_Avg3", "Trailing 3-year average yield for the same combination"],
    ["Area_log", "log(1+Area) — tames the heavy right-skew in cultivated area"],
    ["Years_Since_Start", "Linear year-trend feature"],
  ];
  let cx = 0.6, cw = 2.95, gap = 0.28;
  feats.forEach(([h, b]) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: cx, y: 2.15, w: cw, h: 2.5, rectRadius: 0.12, fill: { color: CARD }, line: { color: "E5E2D8", width: 1 },
    });
    s.addText(h, { x: cx + 0.2, y: 2.35, w: cw - 0.4, h: 0.7, fontFace: FONT_HEAD, fontSize: 15, color: PRIMARY, bold: true });
    s.addText(b, { x: cx + 0.2, y: 3.05, w: cw - 0.4, h: 1.5, fontFace: FONT_BODY, fontSize: 12, color: INK, lineSpacingMultiple: 1.3 });
    cx += cw + gap;
  });

  s.addShape(pres.ShapeType.roundRect, {
    x: 0.6, y: 4.95, w: 12.1, h: 1.55, rectRadius: 0.1, fill: { color: PRIMARY }, line: { type: "none" },
  });
  s.addText("Leakage-safe fill: ~11% of rows lack history (first year a combination appears). These are filled using TRAINING-SET-ONLY crop averages, computed after the train/test split — so no future information leaks backward.", {
    x: 0.95, y: 5.15, w: 11.4, h: 1.2, fontFace: FONT_BODY, fontSize: 13.5, color: "F7F5EF", lineSpacingMultiple: 1.3, valign: "middle",
  });
  pageNum(s, 6);
}

// =========================================================== SLIDE 7 — VALIDATION STRATEGY (timeline)
{
  let s = bgSlide();
  eyebrow(s, "06 · Validation Strategy");
  title(s, "Split by time, not at random");

  // Timeline bar
  const barY = 3.3, barH = 0.9, barX = 0.6, barW = 12.1;
  const trainW = barW * (15 / 18); // 1997-2011 vs 1997-2014 (18 yrs, 15 train)
  s.addShape(pres.ShapeType.roundRect, { x: barX, y: barY, w: trainW, h: barH, rectRadius: 0.06, fill: { color: PRIMARY_LIGHT }, line: { type: "none" } });
  s.addShape(pres.ShapeType.roundRect, { x: barX + trainW, y: barY, w: barW - trainW, h: barH, rectRadius: 0.06, fill: { color: ACCENT }, line: { type: "none" } });
  s.addText("TRAIN  ·  1997 – 2011  ·  40,021 rows", { x: barX, y: barY, w: trainW, h: barH, fontFace: FONT_BODY, fontSize: 13, color: "FFFFFF", bold: true, align: "center", valign: "middle" });
  s.addText("TEST\n2012–14\n9,149 rows", { x: barX + trainW, y: barY, w: barW - trainW, h: barH, fontFace: FONT_BODY, fontSize: 11, color: PRIMARY, bold: true, align: "center", valign: "middle" });

  s.addText("Why not a random split?", { x: 0.6, y: 4.5, w: 6, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, color: PRIMARY, bold: true });
  s.addText([
    { text: "Historical_Yield is a lag feature — a random split would let future years leak into earlier ones", options: { bullet: { code: "25CF" }, breakLine: true } },
    { text: "Preprocessing (scaling, one-hot encoding) fit ONLY on the training fold via sklearn Pipeline + ColumnTransformer", options: { bullet: { code: "25CF" }, breakLine: true } },
    { text: "3-fold cross-validation on the training set adds a stability check alongside the single held-out test score", options: { bullet: { code: "25CF" }, breakLine: true } },
  ], { x: 0.6, y: 4.95, w: 11.9, h: 2.1, fontFace: FONT_BODY, fontSize: 14, color: INK, lineSpacingMultiple: 1.4 });
  pageNum(s, 7);
}

// =========================================================== SLIDE 8 — MODEL COMPARISON (native chart)
{
  let s = bgSlide();
  eyebrow(s, "07–09 · Model Development & Evaluation");
  title(s, "Ten models, tested honestly");

  const modelData = [
    { name: "Test R²", labels: ["LightGBM", "Random Forest", "Gradient Boosting", "XGBoost", "Decision Tree",
        "Ridge", "Lasso", "Linear Reg.", "KNN", "AdaBoost"],
      values: [0.855, 0.854, 0.834, 0.799, 0.776, 0.749, 0.748, 0.747, 0.742, 0.498] },
  ];
  s.addChart(pres.ChartType.bar, modelData, {
    x: 0.6, y: 2.0, w: 12.1, h: 4.5,
    barDir: "col",
    showTitle: true, title: "Test R\u00B2 by Model (held-out 2012\u201314 set)",
    titleFontFace: FONT_HEAD, titleFontSize: 15, titleColor: PRIMARY,
    showLegend: false, showValue: true, dataLabelPosition: "outEnd",
    dataLabelFontSize: 10, dataLabelColor: INK,
    chartColors: [PRIMARY, PRIMARY_LIGHT, ACCENT2, ACCENT2, ACCENT2, MUTED, MUTED, MUTED, MUTED, LOW],
    catAxisLabelFontSize: 10.5, catAxisLabelColor: INK, catAxisLabelRotate: 24,
    valAxisLabelColor: INK, valAxisLabelFontSize: 10, valAxisMinVal: 0, valAxisMaxVal: 1,
    valGridLine: { color: "E5E2D8", size: 0.75 }, catGridLine: { style: "none" },
  });
  pageNum(s, 8);
}

// =========================================================== SLIDE 9 — HONEST FINDINGS
{
  let s = bgSlide();
  eyebrow(s, "07–09 · Model Development & Evaluation");
  title(s, "Two honest findings worth keeping");

  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 2.15, w: 5.85, h: 4.4, rectRadius: 0.14, fill: { color: CARD }, line: { color: LOW, width: 1.5 } });
  s.addText("AdaBoost failed", { x: 0.9, y: 2.4, w: 5.3, h: 0.5, fontFace: FONT_HEAD, fontSize: 18, color: LOW, bold: true });
  s.addText("Cross-validated R\u00B2 = \u22123.47 — a negative score. Its default weak learners and loss weighting are poorly suited to this heavy-tailed, high-cardinality target.", {
    x: 0.9, y: 2.95, w: 5.3, h: 1.5, fontFace: FONT_BODY, fontSize: 14, color: INK, lineSpacingMultiple: 1.35,
  });
  s.addText("It was tested per the assignment's algorithm list, but correctly NOT selected — models were chosen for suitability, not to force a result.", {
    x: 0.9, y: 4.6, w: 5.3, h: 1.7, fontFace: FONT_BODY, fontSize: 13, color: MUTED, italic: true, lineSpacingMultiple: 1.35,
  });

  s.addShape(pres.ShapeType.roundRect, { x: 6.75, y: 2.15, w: 5.95, h: 4.4, rectRadius: 0.14, fill: { color: CARD }, line: { color: ACCENT2, width: 1.5 } });
  s.addText("Tuning didn't win", { x: 7.05, y: 2.4, w: 5.4, h: 0.5, fontFace: FONT_HEAD, fontSize: 18, color: ACCENT2, bold: true });
  s.addText("RandomizedSearchCV tuned LightGBM and Random Forest on training-only CV. Neither tuned config beat the untuned LightGBM baseline (0.855) on the test set.", {
    x: 7.05, y: 2.95, w: 5.4, h: 1.7, fontFace: FONT_BODY, fontSize: 14, color: INK, lineSpacingMultiple: 1.35,
  });
  s.addText("The pipeline automatically keeps whichever model performs best — so the baseline was retained as final, reported as-is rather than forcing an 'improvement'.", {
    x: 7.05, y: 4.75, w: 5.4, h: 1.6, fontFace: FONT_BODY, fontSize: 13, color: MUTED, italic: true, lineSpacingMultiple: 1.35,
  });
  pageNum(s, 9);
}

// =========================================================== SLIDE 10 — FINAL MODEL PERFORMANCE
{
  let s = bgSlide();
  eyebrow(s, "10 · Final Model");
  title(s, "LightGBM — the model in production");

  const metrics = [["0.855", "Test R\u00B2"], ["384.2", "Test RMSE"], ["30.6", "Test MAE"], ["0.108", "Overfit Gap"]];
  let mx = 0.6;
  metrics.forEach(([v, l]) => {
    s.addShape(pres.ShapeType.roundRect, { x: mx, y: 2.1, w: 2.85, h: 1.35, rectRadius: 0.12, fill: { color: PRIMARY } });
    s.addText(v, { x: mx, y: 2.2, w: 2.85, h: 0.7, fontFace: FONT_HEAD, fontSize: 26, color: ACCENT, bold: true, align: "center" });
    s.addText(l.toUpperCase(), { x: mx, y: 2.85, w: 2.85, h: 0.4, fontFace: FONT_BODY, fontSize: 10.5, color: "E7E5DA", align: "center", charSpacing: 1 });
    mx += 3.0;
  });

  s.addImage({ path: FIG("08_actual_vs_predicted.png"), x: 0.6, y: 3.75, w: 4.55, h: 3.35 });
  s.addImage({ path: FIG("10_feature_importance.png"), x: 5.35, y: 3.75, w: 7.35, h: 3.35 });
  pageNum(s, 10);
}

// =========================================================== SLIDE 11 — DISTRICT RANKINGS
{
  let s = bgSlide();
  eyebrow(s, "11 · Prediction & Interpretation");
  title(s, "High- and low-productivity districts");

  s.addImage({ path: FIG("11_district_productivity.png"), x: 0.6, y: 2.05, w: 12.1, h: 4.5 });
  pageNum(s, 11);
}

// =========================================================== SLIDE 12 — RESPONSIBLE AI
{
  let s = bgSlide();
  eyebrow(s, "12 · Responsible AI & Ethics");
  title(s, "What the model shouldn't be trusted for");

  const items = [
    ["No sensitive data", "Only aggregated, public agricultural statistics — no personal information."],
    ["Bias disclosed", "Error varies by state, mostly driven by how many historical records exist per state — disclosed, not hidden."],
    ["Not a guarantee", "Predictions are a planning aid, not a certified yield outcome — never used to unilaterally deny support."],
  ];
  let cx = 0.6, cw = 3.9, gap = 0.25;
  items.forEach(([h, b]) => {
    s.addShape(pres.ShapeType.roundRect, { x: cx, y: 2.2, w: cw, h: 3.9, rectRadius: 0.12, fill: { color: CARD }, line: { color: "E5E2D8", width: 1 } });
    s.addText(h, { x: cx + 0.25, y: 2.5, w: cw - 0.5, h: 0.7, fontFace: FONT_HEAD, fontSize: 16, color: PRIMARY, bold: true });
    s.addText(b, { x: cx + 0.25, y: 3.2, w: cw - 0.5, h: 2.7, fontFace: FONT_BODY, fontSize: 13, color: INK, lineSpacingMultiple: 1.4 });
    cx += cw + gap;
  });
  pageNum(s, 12);
}

// =========================================================== SLIDE 13 — CONCLUSION & FUTURE WORK
{
  let s = bgSlide(PRIMARY);
  s.addShape(pres.ShapeType.ellipse, { x: -1.6, y: -1.6, w: 4.2, h: 4.2, fill: { color: PRIMARY_LIGHT, transparency: 30 }, line: { type: "none" } });
  eyebrow(s, "13–14 · Conclusion & Future Work", { color: ACCENT });
  title(s, "Past performance is the strongest signal we have", { color: "FFFFFF", size: 30 });

  s.addText("The final LightGBM model (Test R\u00B2 = 0.855) confirms district-crop-season history predicts near-term yield better than any structural feature alone.", {
    x: 0.6, y: 2.9, w: 11.5, h: 0.9, fontFace: FONT_BODY, fontSize: 16, color: "E7E5DA", lineSpacingMultiple: 1.3,
  });

  s.addText("Limitations", { x: 0.6, y: 4.0, w: 5.7, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, color: ACCENT, bold: true });
  s.addText([
    { text: "New crop-district combos fall back to a crop average", options: { bullet: { code: "25CF" }, breakLine: true } },
    { text: "Coconut & similar crops use non-tonne units, inflating some districts", options: { bullet: { code: "25CF" }, breakLine: true } },
  ], { x: 0.6, y: 4.4, w: 5.7, h: 1.6, fontFace: FONT_BODY, fontSize: 13, color: "F7F5EF", lineSpacingMultiple: 1.35 });

  s.addText("Future Work", { x: 6.7, y: 4.0, w: 5.7, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, color: ACCENT, bold: true });
  s.addText([
    { text: "Add rainfall & soil-quality data", options: { bullet: { code: "25CF" }, breakLine: true } },
    { text: "Model unit-mismatched crops separately", options: { bullet: { code: "25CF" }, breakLine: true } },
    { text: "Add prediction intervals via quantile regression", options: { bullet: { code: "25CF" }, breakLine: true } },
  ], { x: 6.7, y: 4.4, w: 5.7, h: 1.9, fontFace: FONT_BODY, fontSize: 13, color: "F7F5EF", lineSpacingMultiple: 1.35 });

  s.addText("Dashboard  ·  Notebook  ·  Full pipeline  —  all reproducible via requirements.txt", {
    x: 0.6, y: 6.7, w: 11.5, h: 0.4, fontFace: FONT_BODY, fontSize: 12, color: "9CA595", italic: true,
  });
}

pres.writeFile({ fileName: path.join(__dirname, "..", "reports", "CropYieldPrediction_Presentation.pptx") })
  .then(() => console.log("PPTX created"))
  .catch(err => { console.error(err); process.exit(1); });
