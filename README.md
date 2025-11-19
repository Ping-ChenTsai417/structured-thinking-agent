# structured-thinking-agent

An LLM-powered structured thinking agent. Simply input a real-world scenario, and it outputs a visualized node graph (Mermaid graph) to help you clarify and articulate the problem.

Currently supports two modes:

## 1. ISTJ Model
* **Node Types:**
    * E = Evidence
    * R = Rule
    * X = Risk
    * A = Action
* **Edge Relationships:**
    * E → R (`violates` / `triggers`)
    * E / R → X (`leads_to`)
    * X → A (`mitigate_by`)
* **Use Case:** Answers "What went wrong, why is it serious, and what are the next steps?"

## 2. MECE Model
* **Node Types:**
    * D = Dimension
    * C = Category
    * G = Gap
    * O = Option
* **Edge Relationships:**
    * D → C (`includes`)
    * C → G (`has_gap`)
    * G → O (`resolves_by`)
* **Use Case:** Establishes a complete problem landscape, breaking the situation into parts that are Mutually Exclusive and Collectively Exhaustive (MECE) to facilitate delegation and prioritization.

---

## Installation and Execution

1.  **Install dependencies:**
    ```bash
    pip install langgraph langchain-google-genai google-generativeai
    ```

2.  **Set your Gemini API key** (either directly in the code or using an environment variable).

3.  **Run ISTJ mode:**
    ```bash
    python graph_ISTJ.py
    ```

4.  **Run MECE mode:**
    ```bash
    python graph_MECE.py
    ```

5.  **After execution, two outputs will be generated:**
    * **Terminal:** Prints the nodes and edges analyzed by the LLM.
    * **Project Directory:** A new `.mmd` file (Mermaid) is created.

6.  **View the graph:** Use the "Mermaid Preview" extension in VS Code, or any Mermaid viewer, to open the `.mmd` file and see the relationship graph.
