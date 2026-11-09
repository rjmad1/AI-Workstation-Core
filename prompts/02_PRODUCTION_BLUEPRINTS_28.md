# Production Prompt Template Library: 28 Battle-Tested Blueprints

> **Purpose**: Provide a comprehensive reference library of 28 battle-tested, production-ready prompt templates covering task execution, agent roles, data pipelines, and safety gates.

---

## 1. Core Task Blueprints

### 01. Simple Direct Task
```text
TASK: {task_directive}
CONSTRAINTS:
- Maximum {max_words} words.
- Output ONLY the requested result. No conversational filler.
<INPUT>
{input_text}
</INPUT>
```

### 02. Expert Persona Task
```text
ROLE: {domain_expert_role}
AUDIENCE: {target_audience}
TASK: {complex_task_description}
CONSTRAINTS: Focus on production-grade best practices, failure domains, and concrete implementation details.
```

### 03. Structured Output (JSON Schema)
```text
Extract information from <INPUT> into raw JSON conforming strictly to the schema.
<SCHEMA>
{json_schema}
</SCHEMA>
RULES: Output raw JSON ONLY. No markdown code fences.
<INPUT>
{input_text}
</INPUT>
```

### 04. Few-Shot In-Context Learning
```text
Classify the following text into [{enum_categories}].
EXAMPLES:
Input: "{example_1_input}" -> Output: {example_1_output}
Input: "{example_2_input}" -> Output: {example_2_output}
INPUT: "{target_input}"
OUTPUT:
```

### 05. Intent Classification
```text
Classify user intent into exactly one category: [{intent_list}].
If ambiguous, output "AMBIGUOUS".
<USER_REQUEST>
{user_request}
</USER_REQUEST>
Output JSON: {"intent": "string", "confidence": float}
```

### 06. Entity Extraction
```text
Extract all occurrences of {entity_type} from the document below.
RULES: If none found, return empty array. Do not extrapolate.
<DOCUMENT>
{document_text}
</DOCUMENT>
```

### 07. Compression & Summarization
```text
Condense the document below into exactly {bullet_count} bullet points.
CONSTRAINTS: Preserve all numerical metrics, timestamps, and proper nouns.
<DOCUMENT>
{document_text}
</DOCUMENT>
```

### 08. Code / Data Transformation
```text
Transform the source code from {source_language} to {target_language}.
INVARIANTS:
1. Preserve identical algorithmic complexity ($O(N)$).
2. Preserve error handling semantics.
<SOURCE_CODE>
{code_snippet}
</SOURCE_CODE>
```

---

## 2. Research, Retrieval & RAG Blueprints

### 09. Research Synthesis
```text
Synthesize the multiple source viewpoints below into a balanced Technical Briefing.
Structure: 1. Executive Summary 2. Consensus Findings 3. Conflicting Viewpoints 4. Unresolved Questions.
<SOURCES>
{source_texts}
</SOURCES>
```

### 10. Web Research Investigator (Hermes `investigator`)
```text
ROLE: Investigative Research Specialist.
OBJECTIVE: Find primary source verification for: "{research_claim}".
OUTPUT: Formulate 3 distinct search queries targeting official docs, RFCs, or code repositories.
```

### 11. Document Retrieval QA
```text
Answer the question based strictly on the retrieved text below.
RULES: If the answer is not contained in the text, reply: "NOT AVAILABLE IN CONTEXT".
<CONTEXT>
{retrieved_passages}
</CONTEXT>
QUESTION: {question}
```

### 12. RAG Context Grounding & Citation
```text
Answer the user question. For every factual sentence in your response, append the source citation `[Doc: {filename}#L{line_number}]`.
<GROUNDED_CONTEXT>
{context_chunks}
</GROUNDED_CONTEXT>
QUESTION: {question}
```

---

## 3. Tool & Agent Execution Blueprints

### 13. Tool Use Invocation
```text
You have access to: {tool_schemas}.
Evaluate the user objective: "{user_goal}".
If a tool is required, emit the exact JSON tool call. If not, provide the final answer.
```

### 14. ReAct Agent Decision Loop
```text
Evaluate current task state:
<OBJECTIVE>{user_goal}</OBJECTIVE>
<OBSERVATION_HISTORY>{past_observations}</OBSERVATION_HISTORY>
Produce:
1. Thought: Analysis of current progress and next required action.
2. Action: Tool call `tool_name(args)` OR `FINAL_ANSWER: [text]`.
```

### 15. Task Planner
```text
Decompose the complex goal into an explicit Directed Acyclic Graph of subtasks.
<GOAL>{complex_goal}</GOAL>
OUTPUT: JSON array of steps with `step_id`, `dependencies`, and `acceptance_criteria`.
```

### 16. Sandbox Executor
```text
Execute the designated subtask: "{subtask_description}".
POLICY: Run strictly within workspace sandbox. Do not access external networks.
```

---

## 4. Review, Critic & Verification Blueprints

### 17. Adversarial Critic (Hermes `critic`)
```text
ROLE: Adversarial Red Team Auditor.
Audit the proposed plan below for single points of failure, unstated assumptions, and thundering herd bottlenecks.
Be brutally honest. If flawed, issue REJECT with blocker details.
<PROPOSAL>
{proposal_text}
</PROPOSAL>
```

### 18. Fact Checker / Verifier (Hermes `verifier`)
```text
ROLE: Fact & Citation Verifier.
Audit every claim in <DRAFT> against <SOURCE_TRUTH>.
Flag any unverified claim as [UNVERIFIED] and strip any broken URLs.
```

### 19. Code Reviewer
```text
Review the code diff against: 1. Thread safety 2. Resource leaks 3. SQL/Command injection 4. Performance regressions.
<GIT_DIFF>
{git_diff}
</GIT_DIFF>
```

### 20. Synthesizer (Hermes `synthesizer`)
```text
ROLE: Knowledge Synthesizer.
Reconcile the two conflicting perspectives below into a unified architectural decision matrix.
<VIEWPOINT_A>{text_a}</VIEWPOINT_A>
<VIEWPOINT_B>{text_b}</VIEWPOINT_B>
```

### 21. Self-Refine Pattern
```text
PHASE 1: Write initial draft.
PHASE 2: Audit draft for clarity, conciseness, and edge cases.
PHASE 3: Output final refined version incorporating all fixes.
```

### 22. Verification Audit Gate
```text
Check candidate output against the test assertions: {test_assertions}.
Output: `{"status": "PASSED" | "FAILED", "failed_assertions": []}`.
```

---

## 5. Orchestration, Safety & Routing Blueprints

### 23. Multi-Agent Handoff Contract
```text
Generate a formal handoff payload from {source_bot} to {destination_bot}.
Payload must strictly adhere to the Handoff Schema: {handoff_schema}.
```

### 24. Model Routing Dispatcher (OmniRoute)
```text
Analyze request complexity from 1 to 5 and assign to: [FAST_TIER, CODE_TIER, FRONTIER_TIER].
<REQUEST>{user_request}</REQUEST>
Output raw JSON: {"complexity": int, "route": string, "reason": string}
```

### 25. Ambiguity Resolution Gate
```text
Analyze request: "{user_prompt}".
If any critical technical parameters are missing, STOP. Do NOT write code. Output 3 clarifying questions.
```

### 26. Error Recovery & Repair Link
```text
Fix the runtime syntax error in the payload below.
<ERROR>{runtime_error_message}</ERROR>
<PAYLOAD>{broken_payload}</PAYLOAD>
Output repaired valid payload ONLY.
```

### 27. LLM-as-a-Judge Evaluator
```text
Evaluate candidate output against the 5-point rubric: {rubric_definition}.
Output JSON: {"score": int (1-5), "justification": string}
```

### 28. Benchmark Grader
```text
Compare Model Output A vs Model Output B against Ground Truth Reference.
Determine Winner: [A, B, TIE] with explicit technical justification.
```

---

## Next Step

👉 Proceed to **[37-EVALUATION-TEMPLATE.md](./37-EVALUATION-TEMPLATE.md)** to copy the formal quantitative evaluation rubric and scorecard sheet.
