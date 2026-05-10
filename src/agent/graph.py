# src/agent/graph.py
from langgraph.graph import StateGraph, END
from src.agent.state import FraudInvestigationState
from src.agent.nodes import investigator_node, analyst_node, reporter_node, route_investigation
from src.utils.logger import logger


def build_fraud_investigation_graph():
    logger.info("🏗️ 正在组装专案组工作流图纸...")

    # 1. 初始化图状态 (申请一本全新的案卷夹)
    workflow = StateGraph(FraudInvestigationState)

    # 2. 注册节点 (招募三大探员入列，给他们分配工位名称)
    workflow.add_node("investigator", investigator_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("reporter", reporter_node)

    # 3. 编排工作流 (开始画连线)

    # 专案组的起点：接警后，永远是侦查员先去图数据库取证
    workflow.set_entry_point("investigator")

    # 侦查员查完后，交给路由裁判决定下一步去哪 (核心分流逻辑)
    # add_conditional_edges(当前所在工位, 路由判断函数, {路由返回值: 目标工位})
    workflow.add_conditional_edges(
        "investigator",
        route_investigation,
        {
            "analyst_node": "analyst",  # 裁判说交风控，就传给分析师
            "reporter_node": "reporter"  # 裁判说没线索，就直达报告员
        }
    )

    # 分析师分析完后，把案卷交给报告员写最终报告 (实线直连)
    workflow.add_edge("analyst", "reporter")

    # 报告员写完报告，案卷归档，整个流程结束
    workflow.add_edge("reporter", END)

    # 4. 编译成可执行的工作流引擎
    app = workflow.compile()
    logger.info("✅ 工作流组装完毕，专案组随时可以出警！")
    return app


# ==========================================
# 🚨 探长测试指挥台
# ==========================================
if __name__ == "__main__":
    # 实例化工作流
    app = build_fraud_investigation_graph()

    # 架构师 Tips: 填入我们在 Phase 3 成功查出过数据的账户 ID！
    # 比如 "帮我查一下，有哪些账户向 C1286084959 转过钱？"
    test_query = "帮我查一下，有哪些账户向 C1286084959 转过钱？请进行反欺诈风险评估。"

    print("\n" + "=" * 60)
    print("🚨 指挥中心下达新指令 🚨")
    print("=" * 60)

    # 启动工作流！将初始案件信息装入案卷
    initial_state = {"user_query": test_query}

    # invoke() 会自动驱动引擎，按照你画的图纸一步步跑完，并返回填满的案卷
    final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("🎉 最终呈递探长的红头结案报告 🎉")
    print("=" * 60)
    # 打印最终报告，如果为空就输出兜底文案
    print(final_state.get("final_report", "生成报告失败，请检查日志。"))