#  Fraud-Detective: 企业级智能风控与多智能体审计网络

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)
![Celery](https://img.shields.io/badge/Celery-Distributed-orange)
![Neo4j](https://img.shields.io/badge/Neo4j-GraphDB-blueviolet)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-red)

`Fraud-Detective` 是一个基于 **多智能体 (Multi-Agent)** 架构构建的金融反欺诈审计系统。它模拟了真实银行风控部的“雷达扫描-探员侦查-专家定性-结案报告”全流程。针对传统风控系统在**关系发现难、海量任务堆积、以及大模型数学幻觉**等痛点，提出了基于分布式任务队列与异构数据库解耦的系统级解决方案。

---

## ✨ 核心亮点 (Core Highlights)


### 1. 分布式异步 Agent 引擎 (Production-Ready Scalability)
* **Celery + Redis 异步解耦**：彻底摒弃传统的阻塞式 HTTP 请求。将复杂的 `LangGraph` 状态机执行过程离线化，投递至 **Celery Worker** 节点后台运行。
* **高并发保障**：通过异步任务分发机制，完美解决了大模型长耗时推理导致的 HTTP 连接超时问题，实现了真正可支撑企业级高并发扫描的架构底座。

### 2. “雷达+探员” 异构双库协同 (Dual-DB Synergy)
* **关系型雷达 (MySQL)**：利用 `SQLAlchemy` 对海量交易流水进行高频聚合扫描，利用 OLTP 数据库的极速查询特性，快速锁定触发风控阈值的“头号嫌疑人”。
* **图谱穿透 (Neo4j)**：在锁定嫌疑人后，自动唤醒 **Investigator Agent** 进行 N 度深度资金链路穿透，挖掘隐藏的资金归集与打散等洗钱网络特征。
* **物理级防幻觉策略**：在图谱查询中采用可靠的 2 度链路 Cypher 查询保底，规避 Text2Cypher 的原生语法幻觉，确保证据链的 100% 物理真实，由大模型专注负责复杂特征分析。

### 3. 稳健的 Agentic 状态管理 (Robust Workflow)
* **严格的状态机闭环**：基于 `LangGraph` 构建带状态（Stateful）的专案组工作流，定义了严格的 `CaseState` 卷宗结构，确保线索在探员、分析师、报告员之间传递的强类型约束与无损性。
* **Append-only 消息回溯**：利用 `operator.add` 实现 Agent 思考过程的增量记录，为系统的推理审计和风控决策提供完整的 Trace 溯源链路。

---

##  系统架构设计 (Architecture)

### 1. 业务架构流 (Business Logic)
1. **主动扫描层**：`RadarService` 在 MySQL 中进行高频交易聚合分析，输出嫌疑人初始名单。
2. **异步派单层**：FastAPI 接收请求后，将调查任务编排为 Message 投递至 Redis Broker，交由 Celery 集群消费。
3. **智能体侦查层 (LangGraph)**：
    * **Investigator (侦查员)**：连接 Neo4j 提取结构化资金拓扑情报。
    * **Analyst (分析师)**：基于情报进行多维风险打分与归因定性。
    * **Reporter (报告员)**：结合上下文线索，生成结构化的反洗钱红头报告 (SAR)。
4. **前端展示层**：Streamlit 结合 Plotly 动态轮询任务状态，渲染风控雷达图与调查链路。

### 2. 技术栈概览 (Tech Stack)
* **核心大脑与编排**：`LangGraph` (状态机), `LangChain` (工具与 Prompt 抽象), `Qwen-Max` (LLM)
* **分布式调度**：`Celery` (分布式任务队列), `Redis` (Broker/Backend)
* **后端引擎**：`FastAPI` (全异步接口 API), `SQLAlchemy` (ORM)
* **异构数据底座**：`Neo4j 5.15` (图谱计算), `MySQL 8.0` (关系型流水)
* **前端与数据可视化**：`Streamlit`, `Plotly`, `Streamlit-agraph`

---

##  快速启动 (Quick Start)

项目采用完全容器化部署，可通过 Docker Compose 一键拉起复杂的微服务与双库集群。

### 1. 环境准备
确保本机已安装 `Docker` 与 `Docker Compose`。

### 2. 配置环境变量
```bash
# 复制配置文件模板
cp .env.example .env

# 请在 .env 中填写您的 OPENAI_API_KEY (或兼容格式的大模型 Key)
