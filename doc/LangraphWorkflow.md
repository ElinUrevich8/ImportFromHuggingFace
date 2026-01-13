LangGraph Agentic Workflow Documentation

1. High-Level Architectural Patterns
Based on your provided flowcharts, the agent follows a multi-stage reasoning loop designed for reliability and tool integration.

A. The Core Execution Loop
The basic structure begins with a Plan, followed by iterative cycles of Thought, Action, and Observation until a goal is achieved.

Plan Node: Defines high-level strategies and success criteria.
Thought Node: Performs analytical reasoning based on previous observations and selects the next logical step.
Action Node: Executes specific tool calls (e.g., Trino SQL or Calculator) based on the current thought.
Process Tool Call / Results: Intermediate stages where the system interfaces with external tools and retrieves raw data.
Observe Node: Analyzes raw tool output to determine if information was gained or if errors occurred.
Reflect Node: Critical "self-check" stage that evaluates progress and identifies optimizations or pivots.

B. Recursive Self-Correction
Your architecture supports backtracking. If the Observe or Reflect nodes identify a failure (like a syntax error), the graph directs the flow back to the Thought node to revise the approach rather than ending the process.

2. Node-Specific Responsibilities & Prompts
Each node in your graph operates under specific system constraints to ensure consistency.

NodePrimary ResponsibilityKey Output ElementsPlanGoal Clarification & StrategyAction Plan, Measurable Success Criteria.ThoughtLearning & Next-Step ReasoningLessons Learned, Remaining Needs, Logic for Next Step.ActionTool InvocationAdjusted input based on previous error patterns.ObserveResult AnalysisObservation Summary, Success/Failure status.ReflectOptimizationPerformance critique, Conclude vs. Pivot decision.

3. Execution Logic & Edge Case Handling
Your graph is designed to be resilient against common LLM failure modes, such as infinite loops or hallucinated tool parameters.

Loop Prevention: The Observe and Reflect nodes contain specific instructions to "try something else" if the same failed result occurs across two iterations.
Constraint Following: The Action node is mandated to look for column descriptions and tool constraints before execution to ensure SQL validity.
Variable Mapping: For evaluation (as seen in your Langfuse setup), the system compares the final output against a golden_answer only if a self-correction was successfully performed.

4. Integration with Evaluation (Langfuse)
To monitor these executions, your setup utilizes Variable Mapping to assess performance:

Dataset Mapping: Variables like {{datasetItem.metadata.expected_behavior.golden_answer}} are used to ground the LLM-as-a-judge.
Tone Analysis: Final responses are evaluated not just for accuracy, but for adherence to a predefined professional tone.