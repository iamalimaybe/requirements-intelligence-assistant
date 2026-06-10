# Baseline Evaluation - Qwen3 4B

## Model

qwen3:4b

## Prompt Type

Simple instruction prompt without strict schema, grounding rules, or hallucination controls.

## Runtime Notes

* Response time: 12.5 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Hardware

* CPU: Ryzen 7 5800X
* GPU: RTX 2070 8GB
* RAM: 16GB
* OS: Windows 10

## Prompt

```text
You are a software requirement analyst. Convert this requirement into backend tasks, frontend tasks, database changes, questions for client, and test cases:

Client wants a production report filtered by hierarchy agent and date range. Date filter should use DATE_ADDED and totals should be summed for the selected period.
```

## Raw Model Output

```text
Here's a precise, actionable breakdown as a software requirement analyst. I focused on **clarity, technical feasibility, and avoiding assumptions** while addressing critical ambiguities in the requirement.

---

### 🔍 Critical Questions for Client (Must Answer Before Implementation)
*(These prevent major rework later)*  
1. **What is "hierarchy agent"?**  
   - Is this a *single hierarchical field* (e.g., `agent_hierarchy_level` = "Manager", "Team Lead", "Agent")?  
   - Or a *nested hierarchy* (e.g., a tree structure like `agent_id`, `manager_id`, `team_id`)?  
   *Why it matters:* If it's a nested hierarchy, we need recursive queries or joins. If it's flat, it's simpler.

2. **What metric is being summed?**  
   - The requirement says "totals," but **what is the unit**? (e.g., `production_units`, `revenue`, `calls_processed`?)  
   *Why it matters:* SQL aggregates depend on the metric. Using `SUM(production_units)` vs. `SUM(revenue)` changes the query significantly.

3. **How should `DATE_ADDED` be handled?**  
   - Is `DATE_ADDED` a **timestamp** (e.g., `datetime` column) or **date-only** (e.g., `date` column)?  
   - Should the date filter be **inclusive/exclusive of midnight**? (e.g., `2023-10-01 00:00:00` to `2023-10-02 00:00:00` = 1 day vs. `2023-10-01` to `2023-10-02` = 2 days).  
   *Why it matters:* Date range logic affects query accuracy and edge cases.

4. **Is the "hierarchy agent" filter *per agent* or *per hierarchy level*?**  
   - Example: Should the report show *all agents* under a specific manager (e.g., "Manager A"), or *only agents* with a specific hierarchy level (e.g., "Level 2 agents")?  
   *Why it matters:* This defines whether we need a `WHERE` clause (flat) or a `JOIN`/CTE (hierarchical).

---

### 🛠️ Backend Tasks (Server-Side)
*(Assumes a standard SQL backend like PostgreSQL/MySQL)*

| Task | Description | Why Needed |
|------|-------------|-------------|
| 1. **Add index on `DATE_ADDED`** | `CREATE INDEX idx_date_added ON production_data(DATE_ADDED);` | Critical for performance on date-range queries (avoids full table scans) |
| 2. **Implement date-range filter logic** | Backend API endpoint: `GET /reports/production?start_date=2023-10-01&end_date=2023-10-02&hierarchy_agent=Manager_A` | Converts client date inputs to SQL `BETWEEN` (with time handling) |
| 3. **Handle hierarchy filter** | If hierarchy is flat: `WHERE hierarchy_agent = :hierarchy_value`<br>If nested: Use recursive CTE to filter agents under a specific manager (e.g., `WITH RECURSIVE hierarchy_tree AS (...)`) | Ensures correct agent scope based on client's structure |
| 4. **Aggregate metric** | `SELECT hierarchy_agent, SUM(metric) AS total FROM production_data WHERE DATE_ADDED BETWEEN :start_date AND :end_date ... GROUP BY hierarchy_agent` | Matches "totals summed for selected period" |
| 5. **Validate date inputs** | Reject requests where `end_date < start_date` (return 400 error) | Prevents invalid date ranges |

> 💡 **Key Assumption**: The `production_data` table exists with columns `DATE_ADDED`, `hierarchy_agent`, and the metric (e.g., `production_units`).

---

### 🖥️ Frontend Tasks (Client-Side)
*(Assumes React/Vue/Next.js)*

| Task | Description | Why Needed |
|------|-------------|-------------|
| 1. **Date range picker** | Use a component (e.g., `react-datepicker`) with `start_date` and `end_date` inputs | Lets users select date range |
| 2. **Hierarchy selector** | Dropdown menu or tree view showing *all* hierarchy levels (e.g., "Manager", "Team Lead", "Agent") | Enables filtering by hierarchy level |
| 3. **Filter button** | Button to trigger report fetch with current date/hierarchy values | Executes the backend query |
| 4. **Loading state** | Show spinner when fetching data | Improves UX during network calls |
| 5. **Results display** | Table showing `hierarchy_agent` and `total` (with pagination if >100 records) | Presents aggregated data clearly |

> 💡 **Critical UX Note**: The frontend must **convert user-selected dates to ISO 8601** (e.g., `2023-10-01T00:00:00Z`) to avoid timezone issues in the backend.

---

### 🗃️ Database Changes (Schema Updates)
*(Minimal changes needed if schema exists)*

| Change | Why |
|--------|-----|
| **Add index on `DATE_ADDED`** | Without this, date-range queries become slow (especially for large datasets) |
| **Ensure `hierarchy_agent` is a string/enum** | Avoids type errors in filters (e.g., `hierarchy_agent` should be text, not a number) |
| **No new tables** | The report uses existing tables (no data model changes needed) |

> ⚠️ **If hierarchy is nested**: The backend would need to join with a `hierarchy_table` (e.g., `agents` table with `manager_id`), but the client must confirm this first.

---

### 🧪 Test Cases (Must Cover All Scenarios)
*(Prioritized by criticality)*

| Test Case | Input | Expected Output | Pass/Fail |
|-----------|-------|-----------------|------------|
| 1 | `start_date=2023-10-01`, `end_date=2023-10-01`, `hierarchy_agent=Manager_A` | Total for agents under Manager_A on 2023-10-01 | ✅ |
| 2 | `end_date < start_date` | `400: Invalid date range` | ✅ |
| 3 | `hierarchy_agent=NonExistentLevel` | `0 results` (no agents match) | ✅ |
| 4 | `DATE_ADDED` spans midnight (e.g., `2023-10-01T23:59:59` to `2023-10-02T00:00:00`) | Correctly includes full day (no partial days) | ✅ |
| 5 | `hierarchy` is nested (e.g., Manager A → Team 1 → Agent X) | Shows only Agent X (not Manager A) | ✅ |
| 6 | `0 records` in date range | `0 results` (no totals) | ✅ |
| 7 | `metric` is `revenue` vs `production_units` | Correct aggregation for the chosen metric | ✅ |

> 🔑 **Key test focus**: Date boundaries (midnight handling) and hierarchy depth (nested vs flat) are the most common failure points.

---

### ✅ Summary of Next Steps
1. **Answer the 4 client questions first** (especially Q1 and Q2).  
2. If hierarchy is *nested*, the backend will need a recursive CTE (add 2–3 days of dev time).  
3. **Index on `DATE_ADDED` is non-negotiable** for performance (without it, reports will be slow for >1M records).  
4. All test cases above must pass before deployment.

This breakdown avoids over-engineering while ensuring the solution is **production-ready**. The client gets clear action items without technical jargon. 

Let me know if you'd like to dive deeper into any section (e.g., sample SQL for nested hierarchy, frontend component code)!
```

## Manual Evaluation

### Accuracy

Score: 3 / 5
Notes:
The model identified some valid concerns: the summation field is unknown, date filtering needs care, and test cases are needed. However, it made several incorrect or unsupported assumptions, especially around database engine, table names, hierarchy traversal, frontend framework, endpoint structure, and implementation estimates.

### Grounding

Score: 2 / 5
Notes:
The output is only partially grounded in the prompt. It used the given requirement, but then expanded beyond the available facts by inventing table names, endpoint paths, frontend components, SQL examples, sample values, and database-specific assumptions.

### Hallucination Risk

Score: 2 / 5
Notes:
The hallucination risk is high. The response looks polished and confident, but it mixes valid analysis with invented implementation details. This is dangerous because the output may appear production-ready while being based on assumptions.

### Structure / Format

Score: 4 / 5
Notes:
The response is readable and organized into questions, backend tasks, frontend tasks, database changes, test cases, and next steps. However, the format is not machine-friendly. It does not return structured JSON or dependency-tracked tasks, so it is weak for automation.

### Usefulness for Software Requirements Analysis

Score: 3 / 5
Notes:
The response is useful as a rough human brainstorming output. It is not reliable enough for implementation planning without manual review because too many details are invented or overstated.

## Key Problems Found

| Issue                                     | Why It Matters                                                                                                              |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Assumed PostgreSQL/MySQL                  | The real project context is SQL Server, so PostgreSQL/MySQL assumptions are misleading.                                     |
| Invented table name `production_data`     | A placeholder can be useful, but the model stated it too confidently.                                                       |
| Invented endpoint path                    | The prompt did not provide an API path or naming convention.                                                                |
| Assumed frontend frameworks               | The model mentioned React/Vue/Next.js even though the prompt did not provide frontend technology.                           |
| Assumed nested hierarchy problem          | In the real ticket context, the frontend passes selected `hierarchyAgent`; the report likely should not traverse hierarchy. |
| Recommended recursive CTE                 | This was not grounded in the prompt and may lead to unnecessary complexity.                                                 |
| Added “2–3 days of dev time” estimate     | Unsupported estimate. Looks confident but is not grounded.                                                                  |
| “Index on DATE_ADDED is non-negotiable”   | Too strong. Index may already exist, or the query path may not justify this yet.                                            |
| ISO 8601 `Z` timezone advice              | Could be wrong if the backend uses local dates, SQL Server datetime handling, or integer date formats.                      |
| Used invented sample values               | Values like `Manager_A`, `ABC`, and specific dates were not provided.                                                       |
| Did not mention exact expected inputs     | It did not clearly preserve `companyCode`, `hierarchyAgent`, `startDate`, and `endDate` as the known input contract.        |
| Did not produce implementation-ready JSON | The response is readable but not suitable for direct parsing or automated evaluation.                                       |

## Main Lesson

The answer looks professional, but it mixes useful analysis with invented assumptions. This is exactly the failure mode we need to detect and control when building LLM-based requirement-analysis tools.

## What Should Improve Next

* Add a strict output schema.
* Separate facts, assumptions, unknowns, and client questions.
* Prevent invented table names, endpoint names, frameworks, and sample values.
* Track which tasks are ready versus blocked.
* Track dependencies for each task.
* Add hallucination checks.
* Prefer grounded implementation planning over broad generic advice.
