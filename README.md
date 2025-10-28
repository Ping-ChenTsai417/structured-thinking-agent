# structured-thinking-agent

LLM 驅動的結構化思考代理。你丟一段真實情境，它會輸出一張可視化的節點圖（Mermaid graph），幫你把問題講清楚。

目前支援兩種模式：

## 1. ISTJ 模型
- 節點類型：
  - E = Evidence（事實）
  - R = Rule（規範）
  - X = Risk（風險）
  - A = Action（行動）
- 邊的關係：
  - E → R (`violates` / `triggers`)
  - E / R → X (`leads_to`)
  - X → A (`mitigate_by`)
- 用途：回答「哪裡出問題、為什麼嚴重、下一步怎麼處理」。

## 2. MECE 模型
- 節點類型：
  - D = Dimension（面向）
  - C = Category（子類）
  - G = Gap（缺口）
  - O = Option（修補方案）
- 邊的關係：
  - D → C (`includes`)
  - C → G (`has_gap`)
  - G → O (`resolves_by`)
- 用途：建立完整的問題版圖，把狀況拆成互不重疊、又不遺漏的幾大塊，方便分工和排優先順序。

---

## 安裝與執行

1. 安裝依賴：
   ```bash
   pip install langgraph langchain-google-genai google-generativeai

2. 設定你的 Gemini API key（在程式裡或用環境變數都可以）。

3. 執行 ISTJ 模式：
   ```bash
   python graph_ISTJ.py

4. 執行 MECE 模式：
   ```bash
   python graph_MECE.py
   
5. 執行後會產生兩個輸出：

- 終端機：印出 LLM 分析後的節點 / 邊

- 專案目錄下多一個 .mmd 檔（Mermaid）

6. 用 VS Code 的 Mermaid Preview 外掛，或任何 Mermaid viewer，打開 .mmd 檔就能看到關係圖。
