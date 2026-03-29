---
description: Iterative Task Implementation Workflow with Multi-Agent Review
---

# Multi-Agent Implementation Workflow

This workflow automates the process of building the project by picking up tasks, writing code, rigorously reviewing it through specialized expert personas, testing, and keeping documentation up to date.

## Workflow Steps

**1. Context Gathering & Task Identification:**
- Read the project specification file (`memory-mcp.specify`).
- Read the project task tracker (`task.md`).
- Compare the current state of the codebase against the spec and tracker.
- Select the next uncompleted task from `task.md`. If all tasks are completed, terminate the workflow.

**2. Implementation Phase:**
- Assume the role of the **Implementation Agent**.
- Implement the selected task. This may involve writing code, generating scripts, or configuring files according to the `memory-mcp.specify` guidelines.
- Do not proceed to the next phase until the initial draft of the implementation is fully written.

**3. Quality Review Phase:**
- Assume the roles of three distinct, best-in-class expert sub-agents to review the Implementation Agent's work. Address each review independently:
  - **Code Quality Sub-Agent**: Review the code for cleanliness, maintainability, architectural design, and adherence to best practices (e.g., Clean Code, DRY, SOLID).
  - **Performance Sub-Agent**: Analyze the code for time/space complexity, memory leaks, I/O bottlenecks, and execution efficiency.
  - **Security Sub-Agent**: Audit the code for potential vulnerabilities, attack vectors, data leakage, and insecure dependencies.
- *Handoff / Feedback Loop*: Review the findings. If ANY of the sub-agents report issues, hand the findings back to the **Implementation Agent** to fix the code. Repeat the Quality Review Phase until all three review sub-agents approve the changes.

**4. Testing Phase:**
- Upon approval from the review sub-agents, hand off to the **Testing Sub-Agent**.
- The Testing Sub-Agent must verify the functionality works organically (e.g., writing and running unit tests, or doing manual verifications).
- *Handoff / Feedback Loop*: If testing reveals errors or failures, hand the traceback/errors back to the **Implementation Agent** to fix. The Implementation Agent must re-fix, pass through the Review Sub-Agents again, and return to the Testing Sub-Agent.

**5. Documentation Phase:**
- Once the Testing Sub-Agent gives the final sign-off, update `task.md` to reflect the completed status `[x]` and describe the latest progress.
- Read `README.txt` (create it if it does not exist).
- Update `README.txt` to accurately and completely describe the project as it currently is, encompassing the new features.

**6. Iteration:**
- Move on to the next uncompleted task by looping back to Step 1.
