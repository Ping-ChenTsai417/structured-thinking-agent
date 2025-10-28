'''
MECE 模型
關心 How to divide this question without overlap and without omission（結構化思考）
D = Dimension（面向/維度）

C = Category（該面向下的子類）

G = Gap（這類中發現的缺口/重疊風險）

O = Option（針對該缺口的結構性方案）
------------
D includes → C

C has_gap → G

G resolves_by → O
'''

import json
import re
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. 定義 State：改成 MECE 結構
class MECEState(TypedDict):
    user_situation: str
    dimension_nodes: List[str]   # D1: 人員面
    category_nodes: List[str]    # C1: 責任界定
    gap_nodes: List[str]         # G1: 責任未明確導致延遲
    option_nodes: List[str]      # O1: 建立RACI
    edges: List[Dict[str, str]]  # {"from":"D1","to":"C1","type":"includes"}...
    graph_text: str

# 2. 初始化 Gemini Flash 模型
gemini = ChatGoogleGenerativeAI(
    api_key='AIzaSyDA4qdmteMC5PdkZVxxZuqNUh6_o90jTnY',
    model='gemini-2.5-flash'
)

# Helper: 從 LLM 回傳中抽 JSON
def extract_json(text: str) -> dict:
    # code fence 中的 json
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    # 直接裸 JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    # 最後嘗試整段
    return json.loads(text)

# 3. Node 1: analyze_situation 產生 MECE 節點與分類關係
def analyze_situation(state: MECEState) -> MECEState:
    prompt = f"""
你是一個管理顧問，請用「麥肯錫式 MECE」(Mutually Exclusive, Collectively Exhaustive)
來結構化下面的情境，並輸出純JSON。

重點：不要做因果圖，不要做責備。請做「分類樹」。
MECE 要求：
1. 每個最高層的面向 (Dimension, D) 彼此互斥
2. 這些面向合起來能完整涵蓋問題
3. 每個面向底下再拆成 Category (C) 子類（互斥且能覆蓋該面向）
4. 針對每個子類，列出主要 Gap (G)：缺口/缺陷/風險點
5. 對每個 Gap 提出結構性 Option (O)：怎麼補全或修正

請用以下四種節點類型：
- Dimension_nodes (D): 問題的主要面向，例如「流程面」「溝通面」「人員責任面」
- Category_nodes (C): 每個面向底下的子問題類別，例如「排程規劃」「預警機制」
- Gap_nodes (G): 子類當中暴露出的缺口/不可接受的風險，例如「沒有明確責任歸屬導致延遲」
- Option_nodes (O): 對應的結構性修正方案，例如「建立RACI責任矩陣」「導入延遲預警SOP」

請建立 edges 陣列來描述層級關係：
- D -> C  用 type: "includes"   (這個面向包含這個子類)
- C -> G  用 type: "has_gap"    (這個子類暴露了哪個缺口)
- G -> O  用 type: "resolves_by"(這個缺口可由哪個方案修正)

非常重要：不要輸出因果詞 like "leads_to"、"violates"。我們不是在畫責任，而是在畫分類。

現在的情境如下：
\"\"\"{state['user_situation']}\"\"\" 

請直接輸出嚴格JSON，不要加markdown、不要加註解、不要多餘文字。
JSON格式範例 (只是格式示意，實際內容請依情境產生)：
{{
  "dimension_nodes": [
    "D1: 流程面",
    "D2: 溝通面"
  ],
  "category_nodes": [
    "C1: 排程規劃與里程碑",
    "C2: 延遲預警與回報機制"
  ],
  "gap_nodes": [
    "G1: 沒有定義誰要提早報延遲",
    "G2: 沒有固定進度檢查點"
  ],
  "option_nodes": [
    "O1: 建立固定里程碑審查節奏(每週review)",
    "O2: 規範延遲須於24小時前公告"
  ],
  "edges": [
    {{"from": "D1", "to": "C1", "type": "includes"}},
    {{"from": "D2", "to": "C2", "type": "includes"}},
    {{"from": "C2", "to": "G1", "type": "has_gap"}},
    {{"from": "G1", "to": "O2", "type": "resolves_by"}},
    {{"from": "C1", "to": "G2", "type": "has_gap"}},
    {{"from": "G2", "to": "O1", "type": "resolves_by"}}
  ]
}}
"""

    try:
        resp = gemini.invoke(prompt)

        print("=== Raw LLM Response (repr) ===")
        print(repr(resp))
        print("=== Raw LLM Response (content) ===")
        print(getattr(resp, "content", "<no .content>"))
        print("=" * 50)

        parsed = extract_json(getattr(resp, "content", ""))

        state["dimension_nodes"] = parsed["dimension_nodes"]
        state["category_nodes"] = parsed["category_nodes"]
        state["gap_nodes"] = parsed["gap_nodes"]
        state["option_nodes"] = parsed["option_nodes"]
        state["edges"] = parsed["edges"]

    except Exception as e:
        print(f"[ERROR] {e}")
        raise

    return state

# 4. Node 2: render_graph 轉成 Mermaid 分類樹
def render_graph(state: MECEState) -> MECEState:
    lines = ["graph TD"]

    # D nodes
    for node in state["dimension_nodes"]:
        nid = node.split(":")[0].strip()
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#e1f5ff')  # 淡藍

    # C nodes
    for node in state["category_nodes"]:
        nid = node.split(":")[0].strip()
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#fff9c4')  # 淡黃

    # G nodes
    for node in state["gap_nodes"]:
        nid = node.split(":")[0].strip()
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#ffcdd2')  # 淡紅

    # O nodes
    for node in state["option_nodes"]:
        nid = node.split(":")[0].strip()
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#c8e6c9')  # 淡綠

    # edges
    for edge in state["edges"]:
        src = edge["from"]
        dst = edge["to"]
        etype = edge.get("type", "")
        lines.append(f'  {src} -->|{etype}| {dst}')

    state["graph_text"] = "\n".join(lines)
    return state

# 5. LangGraph workflow
graph_builder = StateGraph(MECEState)
graph_builder.add_node("analyze_situation", analyze_situation)
graph_builder.add_node("render_graph", render_graph)

graph_builder.add_edge(START, "analyze_situation")
graph_builder.add_edge("analyze_situation", "render_graph")
graph_builder.add_edge("render_graph", END)

app = graph_builder.compile()

# 6. 執行
if __name__ == "__main__":
    print("=" * 60)
    print("歡迎使用 MECE 結構化分析工具")
    print("=" * 60)
    print("\nMECE 分析架構（麥肯錫式結構化思考）：")
    print("  Dimension (D) → 問題的主要面向（互斥且完整）")
    print("  Category (C)  → 各面向下的子類別")
    print("  Gap (G)       → 發現的缺口/風險點")
    print("  Option (O)    → 結構性解決方案")
    print("\n請描述你現在面臨的處境或問題：")
    print("(例如：同事三次延遲交付，沒有提前告知，影響客戶時程)")
    print("-" * 60)
    
    user_input = input("\n你現在的處境是什麼？\n> ").strip()
    
    if not user_input:
        print("\n⚠️  未輸入任何內容，使用預設範例...")
        user_input = "同事三次延遲交付，沒有提前告知，影響客戶時程。"
    
    print(f"\n✓ 收到你的情境描述！！")
    print("\n正在進行 MECE 分析，請稍候...\n")
    
    initial_state: MECEState = {
        "user_situation": user_input,
        "dimension_nodes": [],
        "category_nodes": [],
        "gap_nodes": [],
        "option_nodes": [],
        "edges": [],
        "graph_text": ""
    }

    final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print("\n=== Generated MECE Mermaid Graph ===")
    print(final_state["graph_text"])

    with open("mece_analysis.mmd", "w", encoding="utf-8") as f:
        f.write(final_state["graph_text"])
    
    print("\n" + "=" * 60)
    print("✓ Mermaid diagram saved to mece_analysis.mmd")
    print("請使用 Mermaid Live Editor 查看：")
    print("https://mermaid.live/")
    print("=" * 60)