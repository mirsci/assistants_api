---
marp: true
theme: default
paginate: true
---

# Mid-Project Update

## Shopping Assistant Planner - Workstream 2

---

## Context

- This is a summary of the points we have discussed over the last 2 months, put in the context of progress on **Workstream 2** foundational work on **Shopping assistant planner**.

---

## Update

| **Delta Nov. 2026 Release — Workstream 1** | **Foundational Capabilities — Workstream 2** |
| :--- | :--- |
|- We could not prove any reason to fine-tune going into the Oumi engagement, given the definition of functionality for Nov release.<br>- Missing defined ways to measure value differential from fine-tuning (even if there was a reason to fine-tune) <br>- Missing joint definition of architecture lifecycle, model lifecycle and product lifecycle (critical because value is always built incrementally, not one off)<br>- More details see in Issues log tracker TBA| - Working on **systematic baselining of Gemma 4 E4B** for specific functionality (task 3 and 4 as proposed to workstream 1, but de-scoped) <br>- Focused on capabilities and methodology as foundational work but with specific functional targets in mind: <br> 1) data synthesis <br> 2) LLM evals <br> 3) prompt engineering & optimization for the shopping assistant LLM) <br> 4) micro-architecture for the shopping controller (uses the shopping assistant LLM) which enables execution on both server and client without binds to technology like LangGraph |

---

## Key Point 01: Workstream 1 Engagement

**Activities:**
- ✓ Defined plan tasks
- ✓ Collaborated on experimental "every turn intent classification" dataset
- ✓ Analyzed requirements with clarifications
- ✓ Produced inference architecture (engine comparison, deployment fit)
- ✗ Attempted PM engagement on requirements elaboration *(incomplete due to release focus)*

---

## Key Point 02: Workstream Interaction Constraints

**Impact:**
- Workstream interactions curtailed for Nov. release focus
- **Missing ~70% of foundational work value** that would provide residual value for ongoing releases

**See:** Foundational capabilities - Workstream 2 (above)

---

## Key Point 03: External Engagement

**Current situation:**
- Oumi "locked in closet for 2 weeks" design phase
- Work outsourced to Oumi
- Expected **collaboration** based on their LLM lifecycle methodology *not materializing*
  - (Includes data synth and LLM evals)

**Action:** Therefore am returning focus to Workstream 2

---

## Key Point 04: Workstream 2 Breakthrough & Sync Plan

### Breakthrough
Initial success using **Gemma 4 as shopping orchestration planner** with prompt engineering and optimization.

Patricia has asked that I upload code in Github. 
### Current Challenge
- Work is experimental, knowledge context-managed by AI-enabled SDLC
- Method is dynamic and knowledge not yet structured/accessible to team
- Cannot sync effectively at this phase
---

## Path to Synchronization
Wil be working hard to improve this and will follow up with a staged approach:
### Immediate Actions
1. **AI-generated roadmap** as initial reference
2. **Staged maturation** with team updates every **2-3 weeks**
3. **Education roadmap** for required domain knowledge
4. **Definition of Done** for such releases, as it is not a static Github code releases, but a common development integration environment for LLM lifecycle (Patricia and I have talked about this couple of times)

### Follow-up
- Detailed roadmap with code snippets to illustrate approach. The roadmap will have snippets of code to give a sense how the code looks like.

---

## Summary

- Nov. release context set; fine-tuning justification unclear
- Workstream 2 foundational work underway with initial Gemma 4 success
- Knowledge currently embedded in AI-assisted workflow
- Next: structured roadmap and team synchronization in 2-3 week cycles

## Appendix
<img width="812" height="706" alt="image" src="https://github.com/user-attachments/assets/a688fff6-3e13-49a0-a8c7-34f929d1c29b" />
<img width="820" height="762" alt="image" src="https://github.com/user-attachments/assets/3b4ef61b-0ae7-4b5c-aa56-764f0bd2b595" />
<img width="833" height="743" alt="image" src="https://github.com/user-attachments/assets/45068add-d2c5-4d5b-b7c5-4ecfc6ce6918" />

