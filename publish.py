"""검수를 통과한 주제를 갤러리에 올린다(영상 + 썸네일 + 목록 갱신).

  python publish.py themes/saturn.py

gallery/videos/<slug>.mp4, gallery/posters/<slug>.jpg, gallery/manifest.json.
웹사이트 갤러리는 manifest.json만 읽으면 된다.
"""
import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from engine import Renderer  # noqa: E402


def main(theme_path):
    theme_path = Path(theme_path)
    slug = theme_path.stem
    r = Renderer(theme_path)
    th = r.theme
    gal = ROOT / "gallery"
    (gal / "videos").mkdir(parents=True, exist_ok=True)
    (gal / "posters").mkdir(parents=True, exist_ok=True)

    video = gal / "videos" / f"{slug}.mp4"
    poster = gal / "posters" / f"{slug}.jpg"
    r.video(video)
    poster_t = float(getattr(th, "POSTER_T", r.duration * 0.8))
    still = Image.fromarray(r.frame(poster_t))
    still.save(poster, quality=88)
    # 웹 갤러리용 작은 썸네일(540x960)
    web = gal / "posters" / f"{slug}_web.jpg"
    still.resize((540, 960), Image.LANCZOS).save(web, quality=84)

    mpath = gal / "manifest.json"
    items = json.loads(mpath.read_text()) if mpath.exists() else []
    items = [it for it in items if it["slug"] != slug]
    sb = ROOT / "storyboards" / f"{slug}.md"
    items.append({
        "slug": slug,
        "title": getattr(th, "TITLE", slug),
        "duration": r.duration,
        "video": f"videos/{slug}.mp4",
        "poster": f"posters/{slug}.jpg",
        "poster_web": f"posters/{slug}_web.jpg",
        "theme": f"themes/{theme_path.name}",
        "storyboard": f"storyboards/{slug}.md" if sb.exists() else None,
        "size_mb": round(video.stat().st_size / 1e6, 1),
        "updated": date.today().isoformat(),
    })
    items.sort(key=lambda it: it["updated"], reverse=True)
    mpath.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    print(video)
    print(poster)
    print(mpath)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
