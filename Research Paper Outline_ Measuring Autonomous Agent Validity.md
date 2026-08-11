# **Research Summary: Measuring Autonomous Agent Validity**

## **1\. The Problem: The Flaw in Existing Evaluations**

Historically, AI models have been evaluated using single-turn benchmarks (like BLEU or MMLU). However, autonomous software engineering (SWE) agents operate probabilistically over multiple steps, maintaining state and executing tool calls. Because of the **Compounding Error Problem**, an agent with a 1% error rate per reasoning step has a high probability of total failure over long trajectories.  
Furthermore, the current industry shift—driven by spec-driven development generating massive amounts of code—moves the developer's role from writing code to strictly reviewing code. Therefore, an agent's validity cannot solely be based on whether its code compiles; it must be evaluated on whether it actually reduces the developer's review overhead without introducing systemic risk.

## **2\. The Initial Approach: Static Validity & Economics of Review**

We initially derived a static formula to calculate how much a user can believe an agent's output by mathematically binding machine accuracy with human-in-the-loop economics. This is represented as:

$$ V \= \\left( \\prod\_{i=1}^{n} p\_i \\right) \\times C \\times \\max\\left(0, 1 \- \\frac{O\_A}{O\_M}\\right) $$

* **Trajectory Success ($\\prod\_{i=1}^{n} p\_i$):** The compounded probability of success across $n$ tool calls.  
* **Consistency Factor ($C$):** Measured as $pass^{\\wedge}k$, representing how deterministic the agent is across multiple runs of the same task.  
* **Agent Review Overhead ($O\_A$):** The time and cognitive load required for a human to review the agent's Pull Request.  
* **Manual Overhead ($O\_M$):** The time required to manually write the spec and code. If $O\_A \\geq O\_M$, validity drops to zero.

## **3\. The Paradigm Shift: Dynamic Trust Modeling via Calculus**

Because autonomous agents operate over time, static arithmetic is insufficient. We pivoted to using a differential equation to model the system's validity as a continuous flow of state changes. System Validity, $V(t)$, is driven by two competing forces: **Systematic Recovery** (your testing and MCP setup fighting entropy) and **Systematic Decay** (the agent generating unverified complexity).  
This frames trust not as a property of the LLM, but as a property of the surrounding cloud/iPad architecture.

## **4\. Defining and Deriving the System Variables (Proxies)**

### **A. The Degradation Factors (Systematic Decay)**

These variables mathematically pull validity toward zero over time. To be tested empirically, we defined mathematical proxies based on system telemetry:

* **Contextual Entropy ($H\_c(t)$):** Represents context window saturation and error loops. Proxied by the token limit ratio multiplied by the tool failure rate:

  $$ H\_c(t) \= \\left( \\frac{T\_{current}}{T\_{max}} \\right) \\times \\left( 1 \+ \\frac{A\_{fail}(t)}{A\_{total}(t)} \\right) $$  
* **Diff Opacity ($O(t)$):** Measures the human cognitive load required to review the PR. Proxied using Lines of Code, Cyclomatic Complexity, and file spread via AST parsing:

  $$ O(t) \= \\log\_2(1 \+ \\Delta \\text{LOC}) \\times \\left( 1 \+ \\Delta \\text{CC} \\right) \\times N\_{files} $$  
* **Blast Radius / System Coupling ($C$):** The topological risk of the files touched. Proxied via the repository's dependency graph:

  $$ C \= \\frac{D(F\_{changed})}{D\_{total}} $$  
* **Specification Ambiguity ($\\sigma\_{spec}$):** How open-ended the prompt or GitHub label is. Proxied by Semantic Variance (1 minus the cosine similarity of 3 separately generated LLM execution plans).

### **B. The Stabilization Factors (Systematic Recovery)**

These are the architectural guardrails in the automated setup that restore validity toward 1.0:

* **Testing Coverage ($T(t)$):** The strictness and frequency of dedicated frontend and backend spec validation.  
* **MCP Human Alignment Rate ($M(t)$):** The frequency of the agent pausing to ping the user for clarification, which mathematically resets Contextual Entropy.  
* **Deterministic Checkpointing ($\\rho(t)$):** The frequency of atomic, reversible git commits bounding the error scope.  
* **Tool Idempotency ($\\iota$):** The safety of retrying tool calls without corrupting the execution environment.

## **5\. The Final Comprehensive Differential Equation**

Integrating these abstract factors yields the comprehensive formula governing autonomous agent trust over time ($t$):

$$ \\frac{dV}{dt} \= \\underbrace{(1 \- V(t)) \\Big( \\alpha T(t) \+ \\beta M(t) \+ \\gamma \\rho(t) \\iota \\Big)}\_{\\text{Systematic Recovery}} \- \\underbrace{V(t) \\Big( C \\cdot \\sigma\_{spec} \\cdot H\_c(t) \\cdot O(t) \\Big)}\_{\\text{Systematic Decay}} $$

This equation proves mathematically that complex tasks (high Blast Radius and Ambiguity) will rapidly drive system validity to zero unless countered by a robust, heavy infrastructure (frequent MCP alignment and rigid testing).

## **6\. Empirical Methodology Structure**

To defend this model in peer review, the methodology must capture two parallel streams of data across stratified task complexities (Low, Medium, High). This maps the mathematical proxies directly to developer ergonomics:

| Independent Variable (System Telemetry Proxy) | Dependent Variable (Human Ground Truth) | Hypothesis & Validation Method |
| :---- | :---- | :---- |
| Diff Opacity ($O$) | PR Review Time (Minutes) | High opacity predicts longer review times (Pearson correlation). |
| Contextual Entropy ($H\_c$) | PR Abandonment Rate | High entropy predicts the developer will abandon the PR (Logistic Regression). |
| System Coupling / Blast Radius ($C$) | Subjective Trust Score (Likert 1-7) | High coupling decreases trust unless mitigated by perfect test coverage (Spearman Rank). |
| MCP Alignment Rate ($M$) | Subjective Trust Score (Likert 1-7) | Higher alignment frequency directly increases perceived trust. |

