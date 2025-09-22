import time

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from langsmith import traceable
from tools.document_parser import DocumentParser
from tools.compliance_checker import ComplianceChecker
from tools.llm_client import LLMClient
from tools.knowledge_base import KnowledgeBase
from utils.logger import ProcessLogger


class ContractState(TypedDict):
    text: str
    summary: str
    risks: List[Dict]
    compliance: List[str]
    score: int
    knowledge_context: List[Dict]


class ContractReviewAgent:
    def __init__(self):
        self.parser = DocumentParser()
        self.checker = ComplianceChecker()
        self.llm_client = LLMClient()
        self.knowledge_base = KnowledgeBase()
        self.graph = self._build_graph()
        self.logger = None

    def _build_graph(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(ContractState)

        workflow.add_node("parse", self._parse_document)
        workflow.add_node("retrieve_knowledge", self._retrieve_knowledge)
        workflow.add_node("check_compliance", self._check_compliance)
        workflow.add_node("identify_risks", self._identify_risks)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("calculate_score", self._calculate_score)

        workflow.set_entry_point("parse")
        workflow.add_edge("parse", "retrieve_knowledge")
        workflow.add_edge("retrieve_knowledge", "check_compliance")
        workflow.add_edge("check_compliance", "identify_risks")
        workflow.add_edge("identify_risks", "generate_summary")
        workflow.add_edge("generate_summary", "calculate_score")
        workflow.add_edge("calculate_score", END)

        # 去掉debug
        return workflow.compile(debug=False)

    @traceable(name="parse_document")
    def _parse_document(self, state: ContractState) -> ContractState:
        """文档解析节点"""
        if self.logger:
            with self.logger.step("parse", "文档解析", "解析合同文档内容"):
                self.logger.log_input({"text_length": len(state["text"])})
                self.logger.log_progress("正在解析文档结构...")
                self.logger.log_output({"parsed": True})
        return state

    @traceable(name="retrieve_knowledge")
    def _retrieve_knowledge(self, state: ContractState) -> ContractState:
        """知识检索节点"""
        if self.logger:
            with self.logger.step("retrieve", "知识检索", "检索相关法律知识和案例"):
                self.logger.log_progress("正在搜索知识库...")
                knowledge_results = self.knowledge_base.search_relevant_knowledge(state["text"][:1000])
                self.logger.log_metric("检索到的知识条目", len(knowledge_results), "条")
                state["knowledge_context"] = knowledge_results
                self.logger.log_output({"knowledge_count": len(knowledge_results)})
        else:
            knowledge_results = self.knowledge_base.search_relevant_knowledge(state["text"][:1000])
            state["knowledge_context"] = knowledge_results
        return state

    @traceable(name="check_compliance")
    def _check_compliance(self, state: ContractState) -> ContractState:
        """合规性检查节点"""
        if self.logger:
            with self.logger.step("compliance", "合规性检查", "检查合同条款的合规性"):
                self.logger.log_progress("正在执行合规性检查...")
                compliance = self.checker.check_compliance(state["text"])
                self.logger.log_progress("正在获取合规指导...")
                guidance = self.knowledge_base.get_compliance_guidance(state["text"])
                compliance.extend(guidance)
                self.logger.log_metric("合规检查项", len(compliance), "项")
                state["compliance"] = compliance
                self.logger.log_output({"compliance_items": len(compliance)})
        else:
            compliance = self.checker.check_compliance(state["text"])
            guidance = self.knowledge_base.get_compliance_guidance(state["text"])
            compliance.extend(guidance)
            state["compliance"] = compliance
        return state

    @traceable(name="identify_risks")
    def _identify_risks(self, state: ContractState) -> ContractState:
        """风险识别节点"""
        if self.logger:
            with self.logger.step("risks", "风险识别", "识别合同中的潜在风险"):
                self.logger.log_progress("正在分析风险条款...")
                risks = self.checker.identify_risks(state["text"])
                self.logger.log_progress("正在进行风险分析...")
                risk_analysis = self.knowledge_base.get_risk_analysis(state["text"])

                for analysis in risk_analysis:
                    risks.append({
                        "clause": "知识库分析",
                        "issue": analysis["guidance"][:50] + "...",
                        "severity": "medium"
                    })

                high_risks = [r for r in risks if r.get("severity") == "high"]
                if high_risks:
                    self.logger.log_warning(f"发现 {len(high_risks)} 个高风险项")

                self.logger.log_metric("识别风险数量", len(risks), "个")
                state["risks"] = risks
                self.logger.log_output({"risk_count": len(risks), "high_risk_count": len(high_risks)})
        else:
            risks = self.checker.identify_risks(state["text"])
            risk_analysis = self.knowledge_base.get_risk_analysis(state["text"])
            for analysis in risk_analysis:
                risks.append({
                    "clause": "知识库分析",
                    "issue": analysis["guidance"][:50] + "...",
                    "severity": "medium"
                })
            state["risks"] = risks
        return state

    @traceable(name="generate_summary")
    def _generate_summary(self, state: ContractState) -> ContractState:
        """生成摘要节点"""
        if self.logger:
            with self.logger.step("summary", "生成摘要", "基于分析结果生成合同摘要"):
                self.logger.log_progress("正在生成合同摘要...")
                knowledge_context = "\n".join([k["content"] for k in state["knowledge_context"]])
                summary = self.llm_client.generate_summary(state["text"], knowledge_context)
                self.logger.log_metric("摘要长度", len(summary), "字符")
                state["summary"] = summary
                self.logger.log_output({"summary_length": len(summary)})
        else:
            knowledge_context = "\n".join([k["content"] for k in state["knowledge_context"]])
            state["summary"] = self.llm_client.generate_summary(state["text"], knowledge_context)
        return state

    @traceable(name="calculate_score")
    def _calculate_score(self, state: ContractState) -> ContractState:
        """计算评分节点"""
        if self.logger:
            with self.logger.step("score", "风险评分", "计算合同整体风险评分"):
                self.logger.log_progress("正在计算风险评分...")
                score = self.llm_client.calculate_risk_score(
                    state["risks"], state["compliance"]
                )

                if score <= 3:
                    self.logger.log_warning(f"合同风险评分较低: {score}/10")
                elif score >= 8:
                    self.logger.log_progress(f"合同风险评分良好: {score}/10")

                self.logger.log_metric("风险评分", score, "/10")
                state["score"] = score
                self.logger.log_output({"final_score": score})
        else:
            state["score"] = self.llm_client.calculate_risk_score(
                state["risks"], state["compliance"]
            )
        return state

    @traceable(name="analyze_contract")
    def analyze_contract(self, file_path: str) -> Dict:
        """分析合同"""
        self.logger = ProcessLogger("合同审查", f"contract_{int(time.time())}")

        try:
            with self.logger.step("init", "初始化", "准备合同分析环境"):
                self.logger.log_input({"file_path": file_path})

                # 解析文档
                if file_path.endswith('.pdf'):
                    text = self.parser.parse_pdf(file_path)
                elif file_path.endswith('.docx'):
                    text = self.parser.parse_docx(file_path)
                else:
                    text = self.parser.parse_txt(file_path)

                self.logger.log_metric("文档长度", len(text), "字符")

            # 执行工作流
            initial_state = ContractState(
                text=text,
                summary="",
                risks=[],
                compliance=[],
                score=0,
                knowledge_context=[]
            )

            result = self.graph.invoke(initial_state)

            # 打印执行摘要
            self.logger.print_summary()

            return {
                "summary": result["summary"],
                "risks": result["risks"],
                "compliance": result["compliance"],
                "score": result["score"],
                "process_log": self.logger.get_summary()
            }

        except Exception as e:
            self.logger.log_error("合同分析失败", e)
            self.logger.print_summary()
            raise

    async def analyze_contract_stream(self, file_path: str):
        """流式分析合同 - 使用LangGraph流式执行"""
        self.logger = ProcessLogger("合同审查", f"stream_{int(time.time())}")

        try:
            # 解析文档
            yield {"type": "step", "step": "文档解析", "message": "正在解析文档..."}

            if file_path.endswith('.pdf'):
                text = self.parser.parse_pdf(file_path)
            elif file_path.endswith('.docx'):
                text = self.parser.parse_docx(file_path)
            else:
                text = self.parser.parse_txt(file_path)

            yield {"type": "progress", "step": "文档解析", "message": f"文档解析完成，共{len(text)}个字符"}

            # 初始化状态
            initial_state = ContractState(
                text=text,
                summary="",
                risks=[],
                compliance=[],
                score=0,
                knowledge_context=[]
            )

            # 使用LangGraph流式执行
            node_names = {
                "parse": "文档解析",
                "retrieve_knowledge": "知识检索",
                "check_compliance": "合规性检查",
                "identify_risks": "风险识别",
                "generate_summary": "生成摘要",
                "calculate_score": "风险评分"
            }

            final_result = None
            for chunk in self.graph.stream(initial_state):
                for node_name, node_state in chunk.items():
                    if node_name == "__end__":
                        final_result = node_state
                        continue

                    display_name = node_names.get(node_name, node_name)
                    yield {"type": "step", "step": display_name, "message": f"正在执行{display_name}..."}

                    # 根据节点类型提供具体进度信息
                    if node_name == "retrieve_knowledge":
                        knowledge_count = len(node_state.get("knowledge_context", []))
                        yield {"type": "progress", "step": display_name,
                               "message": f"检索到{knowledge_count}条相关知识"}
                    elif node_name == "check_compliance":
                        compliance_count = len(node_state.get("compliance", []))
                        yield {"type": "progress", "step": display_name,
                               "message": f"完成{compliance_count}项合规性检查"}
                    elif node_name == "identify_risks":
                        risks = node_state.get("risks", [])
                        high_risks = [r for r in risks if r.get('severity') == 'high']
                        yield {"type": "progress", "step": display_name,
                               "message": f"识别到{len(risks)}个风险项，其中{len(high_risks)}个高风险"}
                    elif node_name == "generate_summary":
                        yield {"type": "progress", "step": display_name, "message": "摘要生成完成"}
                    elif node_name == "calculate_score":
                        score = node_state.get("score", 0)
                        yield {"type": "progress", "step": display_name, "message": f"风险评分: {score}/10"}

            # 返回最终结果
            if final_result:
                yield {
                    "type": "result",
                    "data": {
                        "summary": final_result.get("summary", ""),
                        "risks": final_result.get("risks", []),
                        "compliance": final_result.get("compliance", []),
                        "score": final_result.get("score", 0)
                    }
                }
            else:
                yield {"type": "error", "message": "工作流执行异常，未获得最终结果"}

        except Exception as e:
            yield {"type": "error", "message": f"分析失败: {str(e)}"}

    @traceable(name="analyze_contract_with_trace")
    def analyze_contract_with_trace(self, file_path: str) -> Dict:
        """分析合同并返回执行轨迹"""
        import time
        self.logger = ProcessLogger("合同审查(详细轨迹)", f"trace_{int(time.time())}")

        try:
            with self.logger.step("init_trace", "初始化轨迹分析", "准备详细轨迹记录"):
                self.logger.log_input({"file_path": file_path})

                # 解析文档
                if file_path.endswith('.pdf'):
                    text = self.parser.parse_pdf(file_path)
                elif file_path.endswith('.docx'):
                    text = self.parser.parse_docx(file_path)
                else:
                    text = self.parser.parse_txt(file_path)

                self.logger.log_metric("文档长度", len(text), "字符")

            # 执行工作流并收集轨迹
            initial_state = ContractState(
                text=text,
                summary="",
                risks=[],
                compliance=[],
                score=0,
                knowledge_context=[]
            )

            with self.logger.step("execute_workflow", "执行工作流", "运行完整的分析流程"):
                # 使用stream收集执行轨迹
                trace_log = []
                final_result = None

                for chunk in self.graph.stream(initial_state):
                    trace_log.append(chunk)
                    if '__end__' in chunk:
                        final_result = chunk['__end__']

                if final_result is None:
                    # 如果没有找到__end__，使用最后一个状态
                    final_result = trace_log[-1] if trace_log else initial_state
                    if isinstance(final_result, dict) and len(final_result) == 1:
                        final_result = list(final_result.values())[0]

                self.logger.log_metric("轨迹步骤数", len(trace_log), "步")

            # 打印执行摘要
            self.logger.print_summary()

            return {
                "summary": final_result.get("summary", ""),
                "risks": final_result.get("risks", []),
                "compliance": final_result.get("compliance", []),
                "score": final_result.get("score", 0),
                "reasoning_trace": trace_log,
                "process_log": self.logger.get_summary(),
                "detailed_trace": self.logger.export_trace()
            }

        except Exception as e:
            self.logger.log_error("轨迹分析失败", e)
            self.logger.print_summary()
            raise
