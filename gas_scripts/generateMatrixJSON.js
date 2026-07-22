function generateMatrixJSON() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // 読み取り元の列（現場_運転目安補足）と書き込み先の列を探す
  const sourceColName = "現場_運転目安補足";
  const targetColName = "マトリックス_JSON"; // 新しく追加する列
  
  const sourceIdx = headers.indexOf(sourceColName);
  let targetIdx = headers.indexOf(targetColName);
  
  if (sourceIdx === -1) {
    SpreadsheetApp.getUi().alert(`エラー: 「${sourceColName}」の列が見つかりません。`);
    return;
  }
  
  // ターゲット列がなければ、右端に新設する
  if (targetIdx === -1) {
    targetIdx = headers.length;
    sheet.getRange(1, targetIdx + 1).setValue(targetColName);
  }
  
  // 判定フラグを自動付与するためのキーワード群（正規表現）
  const regexNG = /禁忌|避けて|推奨されません|禁止|不可|L4|L5|悪化させる恐れ|絶対に避け|競技会時禁止|重篤な/;
  const regexWarn = /注意|慎重|相談|L3|懸念|リスクが増加|過剰摂取により|依存|乱用|監視対象/;
  const regexOK = /安全|L1|L2|第一選択|問題ありませ|影響はありませ|特筆すべき.*ありませ|低いとされま|ありません/;
  
  const categories = ["妊婦・授乳婦", "運転・操作", "禁忌・受診勧奨", "相互作用", "濫用・MOH", "ドーピング・毒性"];
  
  for (let i = 1; i < data.length; i++) {
    const text = data[i][sourceIdx];
    if (!text) continue;
    
    const ingredientsMap = {};
    
    // ① 大項目（カテゴリ）ごとにテキストを分割
    const catRegex = new RegExp(`[・･]<b>(${categories.join('|')})<\\/b>[：:]([\\s\\S]*?)(?=[・･]<b>(?:${categories.join('|')})<\\/b>|$)`, 'g');
    let catMatch;
    
    while ((catMatch = catRegex.exec(text)) !== null) {
      const category = catMatch[1].trim();
      const content = catMatch[2];
      
      // ② カテゴリ内の各成分を抽出
      const ingRegex = /[・･]<b>(.*?)<\/b>[：:]([\s\S]*?)(?=[・･]<b>|$)/g;
      let ingMatch;
      
      while ((ingMatch = ingRegex.exec(content)) !== null) {
        const ingName = ingMatch[1].trim();
        // HTMLの改行タグなどを掃除して純粋なテキストに
        const remark = ingMatch[2].trim().replace(/^<br>\s*/i, '').replace(/<br>/g, '');
        
        if (!ingredientsMap[ingName]) {
          ingredientsMap[ingName] = { "成分名": ingName };
        }
        
// ③ 【改良版】優先順位付きスコアリング（誤検知防止フィルター搭載）
        let judgment = "ー";
        
        // 【ステップA】誤検知の無効化（「禁忌はありません」等が「禁忌」に引っかかるのを防ぐ）
        const sanitizedRemark = remark
          .replace(/禁忌はありません|特筆すべき禁忌.*ありませ[んん]/g, "SAFE_FLAG")
          .replace(/相互作用はありません|特筆すべき相互作用.*ありませ[んん]/g, "SAFE_FLAG")
          .replace(/問題ありません/g, "SAFE_FLAG")
          .replace(/影響はありませ[んん]/g, "SAFE_FLAG");

        // 【ステップB】優先度順の評価
        // 優先度1：【絶対禁忌・レッドフラッグ】何があっても最優先で「✕」
        if (/禁忌|L4|L5|競技会時禁止|使用できません|絶対に避け/.test(sanitizedRemark)) {
          judgment = "✕";
        }
        // 優先度2：【明確なエビデンス（安全）】「避けて」等の一般動詞より優先して「〇」
        else if (/SAFE_FLAG|第一選択|L1|L2|安全|低いとされま|ありません/.test(sanitizedRemark)) {
          judgment = "〇";
        }
        // 優先度3：【原則回避・非推奨】明確な安全基準がない場合の「避けて」等は「✕」
        else if (/推奨されません|避けることが望ましい|避けて|不可/.test(sanitizedRemark)) {
          judgment = "✕"; // ※実務上、OTCで非推奨の場合は「✕」または「△」として扱う
        }
        // 優先度4：【注意喚起・イエローフラッグ】
        else if (/注意|慎重|相談|L3|懸念|リスク|乱用|依存|監視対象/.test(sanitizedRemark)) {
          judgment = "△";
        }
        
        ingredientsMap[ingName][category] = {
          "判定": judgment,
          "備考": remark
        };
      }
    }
    
    // オブジェクトを配列に変換してJSON化
    const finalData = { "成分マトリックス": Object.values(ingredientsMap) };
    
    // スプレッドシートに書き込み
    sheet.getRange(i + 1, targetIdx + 1).setValue(JSON.stringify(finalData, null, 0));
  }
  
  SpreadsheetApp.getUi().alert("✅ JSONの生成が完了しました！「マトリックス_JSON」列を確認してください。");
}