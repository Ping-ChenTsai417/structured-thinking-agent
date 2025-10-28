'''
ISTJ 模型
關心 What happened → Why → So what → Now what（事件分析）
節點（Node）： 
Evidence: E: 客觀事實
Rule: R: 應守標準
Risk: X: 風險/違反點
Action: A: 行動方案

邊（Edges）：
E -> R with "violates" / "triggers"
= 這個事實碰到哪條規範
E -> X / R -> X with "leads_to"
= 這會造成什麼風險
X -> A with "mitigate_by"
= 要用什麼行動來降這個風險
'''
import json
import re
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. 定義 State
class ISTJState(TypedDict):
    user_situation: str
    evidence_nodes: List[str]
    rule_nodes: List[str]
    risk_nodes: List[str]
    action_nodes: List[str]
    edges: List[Dict[str, str]]
    graph_text: str

# 2. 初始化 Gemini Flash 模型
gemini = ChatGoogleGenerativeAI(
    api_key='',
    model='gemini-2.5-flash'
)

# Helper function to extract JSON from LLM response
def extract_json(text: str) -> dict:
    """Extract JSON from text that might contain markdown or extra content."""
    # Try to find JSON in code fences first
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    
    # If all else fails, try parsing the entire text
    return json.loads(text)

# 3. Node 1: analyze_situation
def analyze_situation(state: ISTJState) -> ISTJState:
    prompt = f"""
你是嚴謹的ISTJ決策官。請以ISTJ的結構化判斷風格分析以下情境，並輸出JSON。

情境:
\"\"\"{state['user_situation']}\"\"\" 

說明:
- Evidence(E): 客觀事實、行為紀錄
- Rule(R): 規則/應守標準
- Risk(X): 造成的風險/破壞點
- Action(A): 最小可執行的修正行動（系統層面，不是情緒指責）

建立edges:
- E -> R (type: "triggers" or "violates")
- (E or R) -> X (type: "leads_to")
- X -> A (type: "mitigate_by")

**請直接輸出純JSON，不要加markdown格式或其他說明文字。**

輸出格式範例:
{{
  "evidence_nodes": ["E1:同事三次延遲交付", "E2:沒有提前告知"],
  "rule_nodes": ["R1:交付前應提前通知", "R2:遵守客戶時程"],
  "risk_nodes": ["X1:影響客戶信任", "X2:專案時程失控"],
  "action_nodes": ["A1:建立交付檢查點制度", "A2:設定預警通知機制"],
  "edges": [
    {{"from": "E1", "to": "R2", "type": "violates"}},
    {{"from": "E2", "to": "R1", "type": "violates"}},
    {{"from": "E1", "to": "X1", "type": "leads_to"}},
    {{"from": "X1", "to": "A1", "type": "mitigate_by"}}
  ]
}}
"""

    try:
        resp = gemini.invoke(prompt)
        print("=== Raw LLM Response ===")
        print(resp.content)
        print("=" * 50)
        
        parsed = extract_json(resp.content)
        
        state["evidence_nodes"] = parsed["evidence_nodes"]
        state["rule_nodes"] = parsed["rule_nodes"]
        state["risk_nodes"] = parsed["risk_nodes"]
        state["action_nodes"] = parsed["action_nodes"]
        state["edges"] = parsed["edges"]
        
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response was: {resp.content}")
        raise
    
    return state

# 4. Node 2: render_graph
def render_graph(state: ISTJState) -> ISTJState:
    lines = ["graph TD"]
    
    # 宣告節點並加上樣式
    for node in state["evidence_nodes"]:
        nid = node.split(":")[0]
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#e1f5ff')
    
    for node in state["rule_nodes"]:
        nid = node.split(":")[0]
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#fff9c4')
    
    for node in state["risk_nodes"]:
        nid = node.split(":")[0]
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#ffcdd2')
    
    for node in state["action_nodes"]:
        nid = node.split(":")[0]
        lines.append(f'  {nid}["{node}"]')
        lines.append(f'  style {nid} fill:#c8e6c9')

    # 宣告邊
    for edge in state["edges"]:
        src = edge["from"]
        dst = edge["to"]
        et = edge.get("type", "")
        lines.append(f'  {src} -->|{et}| {dst}')

    state["graph_text"] = "\n".join(lines)
    return state

# 5. 把節點接成一張 LangGraph workflow
graph_builder = StateGraph(ISTJState)
graph_builder.add_node("analyze_situation", analyze_situation)
graph_builder.add_node("render_graph", render_graph)

graph_builder.add_edge(START, "analyze_situation")
graph_builder.add_edge("analyze_situation", "render_graph")
graph_builder.add_edge("render_graph", END)

app = graph_builder.compile()

# 6. 執行
if __name__ == "__main__":
    print("=" * 60)
    print("歡迎使用 ISTJ 結構化事件分析工具")
    print("=" * 60)
    print("\nISTJ 分析架構：")
    print("  Evidence (E) → 客觀事實")
    print("  Rule (R)     → 應守標準")
    print("  Risk (X)     → 風險/違反點")
    print("  Action (A)   → 行動方案")
    print("\n請描述你現在面臨的事件或情境：")
    print("(例如：同事三次延遲交付，沒有提前告知，影響客戶時程)")
    print("-" * 60)
    
    user_input = input("\n你現在的處境是什麼？\n> ").strip()
    
    if not user_input:
        print("\n⚠️  未輸入任何內容，使用預設範例...")
        user_input = "同事三次延遲交付，沒有提前告知，影響客戶時程。"
    
    print(f"\n✓ 收到你的情境描述！！")
    print("\n正在進行 ISTJ 事件分析，請稍候...\n")
    
    initial_state: ISTJState = {
        "user_situation": user_input,
        "evidence_nodes": [],
        "rule_nodes": [],
        "risk_nodes": [],
        "action_nodes": [],
        "edges": [],
        "graph_text": ""
    }

    final_state = app.invoke(initial_state)
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print("\n=== Generated ISTJ Mermaid Graph ===")
    print(final_state["graph_text"])
    
    # 可選：將結果保存到文件
    with open("istj_analysis.mmd", "w", encoding="utf-8") as f:
        f.write(final_state["graph_text"])
    
    print("\n" + "=" * 60)
    print("✓ Mermaid diagram saved to istj_analysis.mmd")
    print("請使用 Mermaid Live Editor 查看：")
    print("https://mermaid.live/")
    print("=" * 60)