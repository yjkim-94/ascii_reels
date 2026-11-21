// 갤러리 웹 빌드: web/ 정적 파일 + gallery 썸네일 + 프롬프트를 dist/로 모은다.
// Vercel buildCommand. 로컬 확인: node web/build.mjs && npx serve dist
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const GAL = join(ROOT, "gallery");
const OUT = join(ROOT, "dist");
const read = (p) => readFileSync(p, "utf8");

rmSync(OUT, { recursive: true, force: true });
mkdirSync(join(OUT, "posters"), { recursive: true });

const manifest = JSON.parse(read(join(GAL, "manifest.json")));
const cards = JSON.parse(read(join(GAL, "cards.json")));
const bySlug = Object.fromEntries(manifest.map((m) => [m.slug, m]));
const base = {
  ko: read(join(GAL, "prompts", "_base.ko.md")).trim(),
  en: read(join(GAL, "prompts", "_base.en.md")).trim(),
};

// 표시 순서 = cards.json 순서. manifest와 프롬프트가 모두 있는 것만 싣는다.
const items = [];
for (const [slug, card] of Object.entries(cards)) {
  const m = bySlug[slug];
  const pk = join(GAL, "prompts", `${slug}.ko.md`);
  const pe = join(GAL, "prompts", `${slug}.en.md`);
  if (!m || !existsSync(pk) || !existsSync(pe)) {
    console.warn(`skip ${slug}: manifest or prompt missing`);
    continue;
  }
  const img = m.poster_web || m.poster;
  cpSync(join(GAL, img), join(OUT, "posters", `${slug}.jpg`));
  items.push({
    slug,
    title: card.title,
    desc: card.desc,
    duration: m.duration,
    poster: `posters/${slug}.jpg`,
    prompt: {
      ko: `${base.ko}\n\n${read(pk).trim()}\n`,
      en: `${base.en}\n\n${read(pe).trim()}\n`,
    },
  });
}

writeFileSync(join(OUT, "data.json"), JSON.stringify({ items }));
for (const f of ["index.html", "style.css", "app.js", "bg.json", "favicon.svg"]) {
  cpSync(join(ROOT, "web", f), join(OUT, f));
}
console.log(`built ${items.length} items -> dist/`);
