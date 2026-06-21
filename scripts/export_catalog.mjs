// Export the hardcoded frontend question schema into a catalog JSON the Django
// backend can seed. Run after any change to the frontend questions:
//   node scripts/export_catalog.mjs [version]
// then:  venv/bin/python manage.py seed_catalog
//
// The frontend stays the single source of truth for questions; this just maps
// them (codes + EN/AR labels) into the backend catalog. Because the onboarding
// app now lives in a separate repo (partners-portal), point this at it via the
// PARTNERS_FRONTEND env var; it defaults to a sibling checkout:
//   <repos>/partners-backend  +  <repos>/partners-portal/partners-frontend

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const version = process.argv[2] || new Date().toISOString().slice(0, 10);

const FRONTEND_DIR =
  process.env.PARTNERS_FRONTEND ||
  path.resolve(__dirname, "..", "..", "partners-portal", "partners-frontend");

const importFrom = (rel) =>
  import(url.pathToFileURL(path.join(FRONTEND_DIR, rel)).href);

const { SCREENS } = await importFrom("src/data/partners.js");
const { default: COUNTRIES } = await importFrom("src/data/countries.js");

const questions = [];
let order = 0;

for (const screen of SCREENS) {
  if (screen.kind !== "fields") continue; // skip welcome / review / confirmation
  for (const f of screen.fields || []) {
    order += 1;
    let options = f.options || null;
    if (f.type === "country") {
      options = COUNTRIES.map((c) => ({ value: c.code, en: c.en, ar: c.ar }));
    }
    questions.push({
      code: f.key,
      type: f.type === "textarea" ? "text" : f.type,
      screen: screen.id,
      order,
      required: !!f.required,
      max_select: f.max || null,
      has_other: !!f.hasOther,
      label_en: (f.label && f.label.en) || "",
      label_ar: (f.label && f.label.ar) || "",
      help_en: (f.helper && f.helper.en) || "",
      help_ar: (f.helper && f.helper.ar) || "",
      options: (options || []).map((o, i) => ({
        code: o.value,
        order: i,
        label_en: o.en,
        label_ar: o.ar,
      })),
    });
  }
}

const closing = SCREENS.find((s) => s.ack);
const acknowledgments = closing
  ? closing.ack.items.map((it) => ({ key: it.key, en: it.en, ar: it.ar }))
  : [];

const out = { version, questions, acknowledgments };
const dest = path.join(__dirname, "..", "catalog", "seed", "catalog.json");
fs.writeFileSync(dest, JSON.stringify(out, null, 2));
const optionCount = questions.reduce((n, q) => n + q.options.length, 0);
console.log(`Wrote version "${version}": ${questions.length} questions, ${optionCount} options -> ${dest}`);
