from pypdf import PdfWriter

# 全5枚を1つのPDFにまとめる。各pageスクリプトの実行後にこれを実行すると、
# 1回の印刷操作でA4・5枚（両面設定はプリンタ側で）が印刷できる。
PAGE_PDFS = [
    "atomic_card_table_v13_page1.pdf",
    "atomic_card_table_v13_page2.pdf",
    "atomic_card_table_v13_page3.pdf",
    "atomic_card_table_v13_page4.pdf",
    "atomic_card_table_v13_page5.pdf",
]
OUTPUT_PDF = "atomic_card_table_v13_全5枚.pdf"

writer = PdfWriter()
for path in PAGE_PDFS:
    writer.append(path)
with open(OUTPUT_PDF, "wb") as f:
    writer.write(f)

print(f"結合完了: {OUTPUT_PDF}（{len(PAGE_PDFS)}ページ）")
