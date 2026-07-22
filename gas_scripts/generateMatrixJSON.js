function generateMatrixJSON() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // 読み取り元の列と書き込み先の列
  const sourceColName = "現場_運転目安補足";
  const maternityColName = "妊婦・授乳婦_専門家エビデンス"; // M列
  const targetColName = "マトリックス_JSON";
  
  const sourceIdx = headers.indexOf(sourceColName);
  const maternityIdx = headers.indexOf(maternityColName);
  let targetIdx = headers.indexOf(targetColName);
  
  if (sourceIdx === -1) {
    SpreadsheetApp.getUi().alert(`エラー: 「${sourceColName}」の列が見つかりません。`);
    return;
  }
  
  if (targetIdx === -1) {
    targetIdx = headers.length;
    sheet.getRange(1, targetIdx + 1).setValue(targetColName);
  }
  
  const categories = ["妊婦・授乳婦", "運転・操作", "禁忌・受診勧奨", "相互作用", "濫用・MOH", "ドーピング・毒性"];
  
  // スコアリング関数
  function evaluateJudgment(text) {
    const sanitizedText = text
      .replace(/禁忌はありません|特筆すべき禁忌.*ありませ[んん]/g, "SAFE_FLAG")
      .replace(/相互作用はありません|特筆すべき相互作用.*ありませ[んん]/g, "SAFE_FLAG")
      .replace(/問題ありません/g, "SAFE_FLAG")
      .replace(/影響はありませ[んん]/g, "SAFE_FLAG");

    if (/禁忌|L4|L5|競技会時禁止|使用できません|絶対に避け/.test(sanitizedText)) {
      return "✕";
    } else if (/SAFE_FLAG|第一選択|L1|L2|安全|低いとされま|ありません/.test(sanitizedText)) {
      return "〇";
    } else if (/推奨されません|避けることが望ましい|避けて|不可/.test(sanitizedText)) {
      return "✕"; 
    } else if (/注意|慎重|相談|L3|懸念|リスク|乱用|依存|監視対象/.test(sanitizedText)) {
      return "△";
    }
    return "ー";
  }
  
  for (let i = 1; i < data.length; i++) {
    const text = data[i][sourceIdx];
    const maternityText = maternityIdx !== -1 ? data[i][maternityIdx] : "";
    if (!text) continue;
    
    const ingredientsMap = {};
    
    // ① 基本データ（現場_運転目安補足）のパース
    const catRegex = new RegExp(`[・･]<b>(${categories.join('|')})<\\/b>[：:]([\\s\\S]*?)(?=[・･]<b>(?:${categories.join('|')})<\\/b>|$)`, 'g');
    let catMatch;
    while ((catMatch = catRegex.exec(text)) !== null) {
      const category = catMatch[1].trim();
      const content = catMatch[2];
      
      const ingRegex = /[・･]<b>(.*?)<\/b>[：:]([\s\S]*?)(?=[・･]<b>|$)/g;
      let ingMatch;
      while ((ingMatch = ingRegex.exec(content)) !== null) {
        const ingName = ingMatch[1].trim();
        const remark = ingMatch[2].trim().replace(/^<br>\s*/i, '').replace(/<br>/g, '');
        
        if (!ingredientsMap[ingName]) ingredientsMap[ingName] = { "成分名": ingName };
        
        ingredientsMap[ingName][category] = {
          "判定": evaluateJudgment(remark),
          "備考": remark
        };
      }
    }
    
    // ② M列（妊婦・授乳婦_専門家エビデンス）での上書き処理
    if (maternityText) {
      const matRegex = /【(.*?)】\s*\((.*?)\)\s*\n([\s\S]*?)(?=(?:【|$))/g;
      let matMatch;
      while ((matMatch = matRegex.exec(maternityText)) !== null) {
        let ingName = matMatch[1].trim();
        
        // ★ クロードさん提案の正規化処理をここに追加 ★
        ingName = ingName.replace('/セネガ', '').replace('乾燥エキス', '乾燥エキス/セネガ');
        
        const evalInfo = matMatch[2].trim();
        const remark = matMatch[3].trim().replace(/\n/g, ''); 
        
        if (!ingredientsMap[ingName]) {
          ingredientsMap[ingName] = { "成分名": ingName };
        }
        
        const combinedTextForEval = evalInfo + " " + remark;
        
        ingredientsMap[ingName]["妊婦・授乳婦"] = {
          "判定": evaluateJudgment(combinedTextForEval),
          "備考": `(${evalInfo}) ${remark}` 
        };
      }
    }
    
    const finalData = { "成分マトリックス": Object.values(ingredientsMap) };
    sheet.getRange(i + 1, targetIdx + 1).setValue(JSON.stringify(finalData, null, 0));
  }
  
  SpreadsheetApp.getUi().alert("✅ 専門家エビデンス(M列)を統合したマトリックスJSONの生成が完了しました！");
}