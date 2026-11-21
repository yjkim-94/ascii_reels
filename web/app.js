// 갤러리 렌더, 한/영 전환, 프롬프트 복사·펼쳐보기, 배경 아스키 배치.
const T = {
  ko: {
    status: "running · Claude Code 추천 · Codex 가능",
    lead: "프롬프트 하나로.",
    sub: "마음에 드는 릴스의 프롬프트를 복사해 Claude Code에 붙여 넣으면, 같은 아스키 릴스가 만들어집니다.",
    copy: "프롬프트 복사",
    copied: "복사됨 ✓",
    view: "프롬프트 보기",
    hide: "접기",
    make_title: "직접 만들기",
    s1_title: "Claude Code 설치",
    s1_body: 'AI 코딩 도구를 설치합니다. <a href="https://code.claude.com/docs" target="_blank" rel="noopener">Claude Code</a>를 추천하고, <a href="https://github.com/openai/codex" target="_blank" rel="noopener">Codex</a>도 쓸 수 있습니다.',
    s2_title: "빈 폴더에서 실행",
    s2_body: "터미널에서 새 폴더를 만들고 그 안에서 실행합니다. Codex라면 <code>claude</code> 대신 <code>codex</code>.",
    s3_title: "프롬프트 붙여 넣기",
    s3_body: "위 갤러리에서 복사한 프롬프트를 붙여 넣습니다. AI가 스토리보드를 먼저 보여 주고, 확인하면 영상(mp4)을 만들어 줍니다.",
    foot: "Python 스크립트 하나로 만든 글자 영상",
  },
  en: {
    status: "running · Claude Code recommended · Codex works too",
    lead: "One prompt.",
    sub: "Copy the prompt of a reel you like, paste it into Claude Code, and get the same ASCII reel.",
    copy: "Copy prompt",
    copied: "Copied ✓",
    view: "View prompt",
    hide: "Hide",
    make_title: "Make your own",
    s1_title: "Install Claude Code",
    s1_body: 'Install an AI coding tool. <a href="https://code.claude.com/docs" target="_blank" rel="noopener">Claude Code</a> is recommended; <a href="https://github.com/openai/codex" target="_blank" rel="noopener">Codex</a> works too.',
    s2_title: "Run it in an empty folder",
    s2_body: "Make a new folder in your terminal and start it there. For Codex, run <code>codex</code> instead of <code>claude</code>.",
    s3_title: "Paste the prompt",
    s3_body: "Paste a prompt copied from the gallery. The AI shows you a storyboard first, and once you approve it renders the video (mp4).",
    foot: "Reels made of letters, from one Python script",
  },
};

let lang = "en";
let items = [];

function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch (e) {
    return null;
  }
}

function pickLang() {
  const saved = store("lang");
  if (saved === "ko" || saved === "en") return saved;
  return (navigator.language || "").toLowerCase().startsWith("ko") ? "ko" : "en";
}

function applyLang(next) {
  lang = next;
  document.documentElement.lang = lang;
  store("lang", lang);
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = T[lang][el.dataset.i18n];
  });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    el.innerHTML = T[lang][el.dataset.i18nHtml];
  });
  document.querySelectorAll(".lang button").forEach((b) => {
    b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
  });
  renderCards();
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}

function renderCards() {
  const root = document.getElementById("gallery");
  const tpl = document.getElementById("card-tpl");
  root.replaceChildren();
  for (const it of items) {
    const node = tpl.content.cloneNode(true);
    const img = node.querySelector("img");
    img.src = it.poster;
    img.alt = `${it.title} – ${it.desc[lang]}`;
    node.querySelector(".title").textContent = it.title;
    node.querySelector(".desc").textContent = it.desc[lang];
    const pre = node.querySelector(".prompt");
    pre.textContent = it.prompt[lang];
    pre.id = `prompt-${it.slug}`;

    const copy = node.querySelector(".copy");
    copy.textContent = T[lang].copy;
    copy.addEventListener("click", async () => {
      const ok = await copyText(it.prompt[lang]);
      if (!ok) return;
      copy.textContent = T[lang].copied;
      copy.classList.add("done");
      setTimeout(() => {
        copy.textContent = T[lang].copy;
        copy.classList.remove("done");
      }, 1800);
    });

    const view = node.querySelector(".view");
    view.textContent = T[lang].view;
    view.setAttribute("aria-controls", pre.id);
    view.addEventListener("click", () => {
      const open = pre.hidden;
      pre.hidden = !open;
      view.setAttribute("aria-expanded", String(open));
      view.textContent = open ? T[lang].hide : T[lang].view;
    });
    root.appendChild(node);
  }
}

// 배경: 시안에서 뽑은 글자 그림을 화면 가장자리 쪽에 흐리게 흩어 둔다
const BG_SPOTS = [
  { x: -6, y: 4, r: -6, dx: 30, dy: -50, c: "#f2b45c" },
  { x: 70, y: 10, r: 5, dx: -40, dy: 30, c: "#7aa7ff" },
  { x: 74, y: 58, r: -4, dx: -20, dy: -40, c: "#bcd4ff" },
  { x: -8, y: 62, r: 7, dx: 40, dy: 20, c: "#5fe08a" },
];

async function placeBackground() {
  try {
    const res = await fetch("/bg.json");
    const arts = await res.json();
    const bg = document.getElementById("bg");
    arts.forEach((a, i) => {
      const s = BG_SPOTS[i % BG_SPOTS.length];
      const pre = document.createElement("pre");
      pre.textContent = a.text;
      pre.style.left = `${s.x}vw`;
      pre.style.top = `${s.y}vh`;
      pre.style.color = s.c;
      pre.style.setProperty("--r", `${s.r}deg`);
      pre.style.setProperty("--dx", `${s.dx}px`);
      pre.style.setProperty("--dy", `${s.dy}px`);
      pre.style.animationDelay = `${-i * 7}s`;
      bg.appendChild(pre);
    });
  } catch (e) {
    /* 배경은 장식이라 실패해도 그냥 둔다 */
  }
}

async function main() {
  document.querySelectorAll(".lang button").forEach((b) => {
    b.addEventListener("click", () => applyLang(b.dataset.lang));
  });
  try {
    const res = await fetch("/data.json");
    items = (await res.json()).items;
  } catch (e) {
    items = [];
  }
  applyLang(pickLang());
  placeBackground();
}

main();
