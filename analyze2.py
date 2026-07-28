import re

with open("pharma_dictionary_compiled.html", encoding="utf-8") as f:
    html = f.read()

# h2とh3両方を分割点にする
sections = re.split(r'(?=<h[23][^>]*>)', html)

TARGET_INGREDIENTS = ["エフェドリン","コデイン","ジヒドロコデイン","ブロモバレリル尿素",
                       "プソイドエフェドリン","メチルエフェドリン","デキストロメトルファン","ジフェンヒドラミン"]
CATEGORIES = ["妊婦","授乳","運転","禁忌","相互作用","濫用","MOH","ドーピング","半減期"]

rows = []
for sec in sections:
    m = re.match(r'<h([23])[^>]*>(.*?)</h[23]>', sec, re.DOTALL)
    if not m:
        continue
    level = "H2" if m.group(1) == "2" else "  H3"
    title = re.sub(r'<.*?>', '', m.group(2)).strip()[:40]
    body = re.sub(r'<.*?>', '', sec)
    length = len(body)
    ing_hits = [i for i in TARGET_INGREDIENTS if i in body]
    cat_hits = [c for c in CATEGORIES if c in body]
    flag = "★情報薄い" if length < 150 and level.strip() == "H3" else ""
    rows.append((level, title, length, len(ing_hits), len(cat_hits), flag))

print(f"{'Lv':<5}{'見出し':<42}{'文字数':>7}{'成分':>6}{'ｶﾃｺﾞﾘ':>7}  備考")
print("-" * 90)
for r in rows:
    print(f"{r[0]:<5}{r[1]:<42}{r[2]:>7}{r[3]:>6}{r[4]:>7}  {r[5]}")
