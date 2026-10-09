# pharma-gatekeeper

> [!IMPORTANT]
> **【開発者・運用者への重要なお知らせ：新製品追加時の注意】**
>
> 1. **【剤形による用量違いの罠】**
>    「シリーズ名」だけで一括管理してはいけません。同じ「ベンザブロックプラス」という名称でも、『カプレット（細長）』と『錠（円形）』で1回あたりの服用錠数が異なり、結果として「1日最大服用量」が変わるケースが多発しています。必ず**【実物のパッケージ】**または**【最新の添付文書】**を確認し、剤形ごとに別IDで定義してください。
>
> 2. **【1日最大量の算出基準】**
>    用法用量に「適宜増減」とある場合も、必ず**【認められている最大の用法・用量】**を `dailyDose` に設定してください。
>
> 3. **【判定の根拠】**
>    このマスタの各数値は、実物のパッケージ・最新の添付文書で確認した値に一致させること。判定ロジックの一次ソースは `package_verification.csv`。

## このリポジトリの概要

薬局（ミアヘルサ薬局）の「指定濫用防止医薬品」販売ルール遵守のための、レジ担当者向け参考資料（A4・全5枚、PNG/PDF）と、独立したWeb版参考アプリを管理しています。
複数のClaudeスレッドが並行作業しているため、作業前に `CLAUDE.md` と `WISHLIST.md` を確認してください。

## パイプライン

```mermaid
flowchart LR
    DU[data_updated.csv<br/>成分・用法用量などの製品データ] --> EX[extract_package_data_v2.py 等<br/>オフライン生成スクリプト]
    CF[confusing_medicines_reference.csv<br/>紛らわしい薬の参照] --> EX
    EX --> PV[package_verification.csv<br/>早見表の判定ロジックの一次ソース]
    PV --> P1[vpc_v13_page1.py]
    P1 --> OUT[atomic_card_table_v13_pageN.png / .pdf<br/>A4 全5枚]
    P2["vpc_v13_page2〜5.py<br/>（page5はproject-thread-5md6eqブランチ）"] -.->|CSVを読まず自己完結| OUT
    DU --> BF[build_final.py など]
    BF --> IDX[index.html<br/>window.medicineMaster を埋め込み生成]
    PS[print_style.py<br/>印刷フォント6pt下限保証] -.->|project-thread-67zu13ブランチのみ導入済み、未マージ| P1
```

- `package_verification.csv` を実際にCSVとして読み込むのは `vpc_v13_page1.py` だけです。2〜5枚目のスクリプトはCSVを読まず、Python内に直接データを持つ自己完結型です（4・5枚目の本文中に `package_verification.csv` への言及はありますが、あくまる説明文であり読み込みではありません）。
- 各ページは `python vpc_v13_pageN.py` で `atomic_card_table_v13_pageN.png` / `.pdf` を出力します（matplotlib）。
- `data_updated.csv` と `confusing_medicines_reference.csv` は `vpc_v13_page*.py` からは直接読まれません。`extract_package_data_v2.py` / `extract_package_data_with_confusing.py` などのオフライン生成スクリプトが読み込んで `package_verification.csv` を再生成する入力データです。
- `index.html` は上記スクリプトとは独立して動作するWebアプリで、CSVをその場では読みません。`build_final.py`（旧 `build.py`）が `data_updated.csv` を読み込み、`window.medicineMaster = {...}` という埋め込みJSONを生成して `index.html` に書き込んでいます。
- `print_style.py` は印刷時フォントサイズ6pt下限を保証する共通モジュールです。現時点では `project-thread-67zu13` ブランチにのみ導入されており、`main` にはまだマージされていません。

## CSVの区分

### 生きているファイル（編集・参照の対象）

| ファイル | 役割 |
|---|---|
| `package_verification.csv` | 早見表（1枚目）の判定ロジックの一次ソース。`vpc_v13_page1.py` が直接読み込む唯一のCSV |
| `data_updated.csv` | 成分・用法用量などの製品データ。`package_verification.csv` と `index.html` 埋め込みデータの元になるオフライン生成の入力 |
| `提出用_指定濫用マスタ.csv` | 提出用マスタ |
| `confusing_medicines_reference.csv` | 紛らわしい医薬品の参照表（`package_verification.csv` 生成時の入力の一つ） |

### 中間生成物・過去の作業ファイル（原則そのまま。新規の判定には使わない）

`data.csv` / `Dify連携.csv` / `0724_14 - URL付きﾘｽﾄ.csv` / `otc_master_updates_abuse_prevention.csv` / `otc_master_updates_abuse_prevention_corrected.csv` / `otc_master_updates_abuse_prevention_normalized.csv` / `package_judgment_validation_report.csv` / `package_judgment_validation_report_v2.csv`

これらは `build*.py`、`validate_package_judgment*.py`、`normalize_package_product_names.py` などの過去スクリプトが生成・使用したものです。
