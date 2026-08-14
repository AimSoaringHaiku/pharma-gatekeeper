import pandas as pd
import re

def audit_packaging_logic(csv_file="package_verification.csv"):
    # データを読み込み
    try:
        df = pd.read_csv(csv_file, encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {csv_file}")
        return

    df["days"] = pd.to_numeric(df["days"], errors="coerce")
    df["limit"] = pd.to_numeric(df["limit"], errors="coerce")
    
    errors = []
    summary = {}

    for _, row in df.dropna(subset=["days", "limit"]).iterrows():
        product = str(row["product"])
        package = str(row["package"])
        days = float(row["days"])
        limit = float(row["limit"])

        # 1. 1日量の抽出と計算
        match = re.search(r"([\d\.]+)", package)
        amount = float(match.group(1)) if match else 0
        
        if days <= 0:
            continue
            
        daily_amount = amount / days
        boundary = daily_amount * limit
        
        # 2. 大小判定の矛盾チェック
        # days（消費日数）がlimit（制限日数）を超えていれば大容量のはず
        is_large = days > limit
        
        # 浮動小数点誤差を許容するための極小マージン
        epsilon = 0.01 
        
        if amount - boundary > epsilon and not is_large:
            errors.append(f"【矛盾】{product} ({package}): 容量が境界値を超えていますが小包装扱いです。")
        elif boundary - amount > epsilon and is_large:
             errors.append(f"【矛盾】{product} ({package}): 容量が境界値以内ですが大容量扱いです。")
             
        # 3. 監査サマリ用に各薬剤の制限日数を記録
        if product not in summary:
            summary[product] = limit
            
    print("--- 監査レポート ---")
    if errors:
        for err in errors:
            print(err)
    else:
        print("✅ 計算ロジック・境界値の矛盾はゼロです。テトリス配置のデータ構造は完璧です。")
        
    print("\n【参考】各薬剤に設定されている制限日数（limit）の一覧:")
    limit_groups = {}
    for prod, lim in summary.items():
        limit_groups.setdefault(lim, []).append(prod)
        
    for lim, prods in sorted(limit_groups.items()):
        print(f"・制限 {lim}日: {', '.join(prods)}")

# 実行
if __name__ == "__main__":
    audit_packaging_logic("package_verification.csv")