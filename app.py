# app.py

from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ==========================================
# 1. 定义 State (状态/共享内存)
# ==========================================
class CodingState(TypedDict):
    task: str                               # 原始需求
    code: str                               # 当前代码
    review_verdict: Literal["pass", "fail"] # 审查结论
    review_feedback: str                    # 审查反馈
    retry_count: int                        # 已重试次数
    max_retries: int                        # 最大重试次数

# ==========================================
# 2. 定义 Node (节点/处理函数)
# ==========================================
def generate_node(state: CodingState) -> dict:
    """节点1：根据需求生成初始代码"""
    print(f"\n--- [Node] 开始生成代码，任务: {state['task']} ---")
    # 模拟大模型生成，故意生成一个带有 TODO 的废代码，为了让后面触发重试
    code = f"# TODO: implement: {state['task']}\npass"
    return {"code": code}

def review_node(state: CodingState) -> dict:
    """节点2：审查代码"""
    print(f"\n--- [Node] 开始审查代码 ---")
    code = state["code"]
    # 模拟审查逻辑：如果代码里还有 TODO 就判定失败
    if "pass" in code and "TODO" not in code:
        print("审查结果：通过！")
        return {"review_verdict": "pass", "review_feedback": ""}
    
    print("审查结果：不通过，代码还是个半成品。")
    return {
        "review_verdict": "fail",
        "review_feedback": "代码仍包含 TODO 占位，请实现具体逻辑。",
    }

def revise_node(state: CodingState) -> dict:
    """节点3：根据反馈修改代码，并消耗一次重试次数"""
    print(f"\n--- [Node] 收到反馈，开始修改代码。当前重试次数: {state['retry_count']} ---")
    feedback = state["review_feedback"]
    # 模拟修改：把 TODO 去掉，生成能跑的代码
    new_code = f"# 修改依据: {feedback}\nprint('功能已实现')"
    return {
        "code": new_code,
        "retry_count": state["retry_count"] + 1, # 重点：重试次数+1
    }

# ==========================================
# 3. 定义 Edge (边/路由逻辑)
# ==========================================
def route_after_review(state: CodingState) -> str:
    """条件边：审查完之后的走向决策"""
    print(f"--- [Router] 判定下一步走向 ---")
    if state["review_verdict"] == "pass":
        print("-> 走向: 结束 (END)")
        return "end"
    if state["retry_count"] >= state["max_retries"]:
        print("-> 走向: 超过最大重试次数，强制结束")
        return "end"
    
    print("-> 走向: 打回修改 (revise)")
    return "revise"

# ==========================================
# 4. 构建 Graph (拼装积木)
# ==========================================
print(">>> 正在构建流程图...")
builder = StateGraph(CodingState)

# 4.1 添加所有节点
builder.add_node("generate", generate_node)
builder.add_node("review", review_node)
builder.add_node("revise", revise_node)

# 4.2 连线 (普通边)
builder.add_edge(START, "generate")
builder.add_edge("generate", "review")
builder.add_edge("revise", "review") # 注意这里，修改完之后再次进入审查节点，形成循环

# 4.3 连线 (条件边)
builder.add_conditional_edges(
    "review",             # 从 review 节点出发
    route_after_review,   # 经过路由函数判定
    {
        "end": END,       # 如果返回 "end"，就走向结束
        "revise": "revise"# 如果返回 "revise"，就走向修改节点
    }
)

# 编译图
graph = builder.compile()
graph.get_graph().draw_mermaid_png(output_file_path="architecture_graph.png")
print(">>> 流程图构建成功！\n")

# ==========================================
# 5. 运行 Demo
# ==========================================
if __name__ == "__main__":
    # 初始化状态数据
    initial_state = {
        "task": "写一个计算两数之和的函数",
        "code": "",
        "review_verdict": "fail",
        "review_feedback": "",
        "retry_count": 0,
        "max_retries": 2, # 最多允许重试2次
    }

    print("========== 开始执行工作流 ==========")
    # 启动图
    result = graph.invoke(initial_state, {"recursion_limit": 10})
    
    print("\n========== 执行结束 ==========")
    print(f"最终产出的代码:\n{result['code']}")
    print(f"总共重试了 {result['retry_count']} 次")
    print(f"最终审查状态: {result['review_verdict']}")