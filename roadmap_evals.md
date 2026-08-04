---
marp: true
theme: default
class: invert
paginate: true
footer: "Hybrid-AI Shopping Assistant | Implementation Roadmap"
---

#  Hybrid-AI Shopping Assistant 
## Implementation Roadmap


---

## Executive Summary

### The Problem
- **Current:** Experimental / manual testing/evals, ad-hoc prompts, no systematic SLM evolution workflow, shopping functionality in-flux 


### The Solution
- Automated multi-layer evaluation with DeepEval
- Spec based data synthesis (including with Oumi)
- Prompt engineering & optimization
- Rules based orchestration
- Use design techniques to avoid compositional learning and make possible hybrid orchestration
- **1,024+ synthetic test scenarios** systematically covering compositional paths
- **CI/CD gates** preventing regressions before deployment

---

# Phase 1: Schema Contract Definition
## Foundation for All Evaluation

**Duration:** 8-17 days | **Risk if Skipped:** 🔴 **HIGH**

### Without Schema Contract
- ❌ Can't distinguish broken model vs policy violation vs quality issue
- ❌ Invalid JSON wastes judge LLM calls
- ❌ Enum drift undetected ("Prepare MerchantSearch" becomes prose)
- ❌ Silent failures in downstream systems

### With Schema Contract
- ✅ Fail-fast detection (<1 second per violation)
- ✅ Engineering clarity on output shape
- ✅ Maintainable code and prompts aligned to business domain
- ✅ Downstream automation enabled

---

## Phase 1: Implementation

**BAML Schema Definition**
```baml
/// Shopping assistant response to user.
class ShoppingResponse {
  action string @description("Action: clarify, recommend, compare, no_results, off_domain")
  message string @description("Natural language response")
  slots ProductSlots? @description("Current product requirements")
  products Product[]? @description("Product recommendations")
  offers MerchantOffer[]? @description("Merchant offers")
  clarification_question string? @description("Clarification question if needed")
}
```

**Hard Gates**
- Schema compliance: 0.0 if invalid JSON
- Enum compliance: 0.0 if not valid enum
- Non-null gate: 0.0 if shopper_response missing

---

# Phase 2: Rule Evaluation Metrics
## Validating Business Logic

**Duration:** 13-20 days | **Risk if Skipped:** 🔴 **HIGH**

### Business Rules (r01-r04)
- **r01:** Keep clarifying until 3+ slots extracted
- **r02:** Trigger MerchantSearch on brand/merchant criteria
- **r03:** Trigger OfferSearch for high-value shoppers
- **r04:** Gate CatalogSearch until readiness met

### If Rules Break
- ❌ Premature search → irrelevant results
- ❌ Missed merchant criteria → lost cashback
- ❌ Skipped clarification → size/fit problems

### Rule Metrics Catch
- ✅ Rule accuracy (target >90%)
- ✅ Rule precedence issues (target >95%)
- ✅ Conflicting activations (target <2%)

---

## Phase 2: Key Metrics

**TriggerRuleAccuracyMetric**
- For each rule (r01-r04): does it trigger when it should?
- Scoring: % correct / total rules evaluated

**RulePrecedenceMetric**
- r02 merchant criteria overrides r04.02.01 (all-catalog search)
- r04.02.02 blocks catalog search until merchant selection
- Scoring: 1.0 - (violations / precedence pairs)

---

# Phase 3: Trace-Based Evaluation
## End-to-End Workflow Validation

**Duration:** 14-21 days | **Risk if Skipped:** 🟡 **HIGH**

### Why Trace Evaluation?
- Correct slots ≠ correct next_action
- Correct trigger ≠ proper blocking
- Multi-turn requires accumulated state

### FixtureSpec = Deterministic Ground Truth
```yaml
input_turns:
  - "I need a comfy sweater"
  - "earthy tones please"
  - "she likes trekking"

expected_trace:
  turn_0: needs_clarification (2/3 slots)
  turn_1: needs_clarification (3/3 slots, color added)
  turn_2: complete → ProductCatalogSearch ready
```

### Success Metrics
- Trace alignment: >85%
- Slot extraction: >90%
- Next action: >95%

---

# Phase 4: Multi-Turn Conversational Eval
## Realistic Shopping Flows

**Duration:** 13-20 days | **Risk if Skipped:** 🟡 **HIGH**

### Conversation Dynamics
1. "I need running shoes" → ProductDiscovery
2. "What size?" → Clarification
3. "Size 10, Nike preferred" → Slots updated, MerchantSearch triggered
4. "Pickup available?" → ContextTracking
5. "Curbside works" → Final state → CatalogSearch

### Multi-Turn Tests Validate
- ✅ Slots persist across turns
- ✅ State updates correctly
- ✅ Corrections applied properly
- ✅ Intent lifecycle handled

### Success Metrics
- Multi-turn pass: >80%
- State consistency: >90%
- Correction handling: >85%

---

# Phase 5: Composite Metric

**Duration:** 10-15 days | **Risk if Skipped:** 🟢 **MEDIUM**

### Three-Layer Evaluation
```
Layer 1 (Hard Gates)        → Must be 100%
  Schema valid? Enum valid? Non-null?
           ↓
Layer 2 (Rule Accuracy)     → Target >90%
  Do rules trigger correctly?
           ↓
Layer 3 (Quality)           → Target >80%
           ↓
FINAL SCORE (0.0-1.0)       → Release gate: 0.75+
```
  Trace alignment? Response quality?

### Why Single Metric?
- ✅ One threshold for go/no-go decisions
- ✅ Weighted priorities visible
- ✅ Failure analysis built-in
- ✅ Historical trending enabled

---

# Phase 6: Test Data Synthesis/Generation
## 1,024+ Synthetic Scenarios

**Duration:** 18-24 days | **Risk if Skipped:** 🔴 **HIGH**

### Attribute Grid
```
Route type          × 4 variants
Product category    × 4 variants
Slot completeness   × 4 variants
Merchant criteria   × 4 variants
Adversarial pattern × 4 variants
─────────────────────────────────
TOTAL: 4⁵ = 1,024 combinations
```

### Why Automated Synthesis?
- ❌ Manual: Hours per case, error-prone
- ✅ Generated: <5 minutes, systematic, reproducible, adaptable with evolving domain logic, application functionalityand design.

### Adversarial Coverage
- Vocabulary slippage ("prepare merchant" instead of enum)
- Schema probes (request specific JSON fields)
- Rule conflicts (r02 + r04.02.01 simultaneously)

---

# Phase 7: Prompt Optimization
## Learnable Prompt Improvement

**Duration:** 12-20 days | **Risk if Skipped:** 🟢 **MEDIUM**

### Traditional Loop (❌ Slow)
1. Run eval → see failures
2. Manually tweak prompt
3. Re-run eval → hope it improves
4. Repeat 5-10x per month

### Optimized Loop (✅ Fast)
1. Define metric (ControllerAdapterMetric)
2. Run MIPROv2 optimizer
3. System discovers better prompts automatically
4. Deploy optimized prompts
5. Repeat weekly

### Expected Gains
- **5-10% improvement** vs. baseline
- **2 hours** per optimization run
- **10-20% faster** iteration velocity

---

# Phase 8: CI/CD Integration
## Automated Quality Gates

**Duration:** 12-22 days | **Risk if Skipped:** 🔴 **HIGH**

### Without CI/CD Gates
- ❌ Engineers manually remember to run evals (they don't)
- ❌ Regressions slip to production
- ❌ Quality degrades silently over time
- ❌ Release decisions subjective

### With CI/CD Gates
- ✅ Every PR gets automatic eval feedback
- ✅ Regressions block merge (0.75 threshold)
- ✅ Quality trends visible in dashboards
- ✅ Data-driven release decisions

---


## Risk Mitigation

### What We're Protecting Against

| Risk | Consequence | Mitigation |
|------|-------------|-----------|
| **Silent rule drift** | Wrong decisions in production | Automated regression detection |
| **Enum backsliding** | Model outputs prose instead of vocabulary | Hard gate (0.0 score immediately) |
| **State loss** | Slots forgotten between turns | Multi-turn trace validation |
| **Precedence bugs** | r02 conflicts with r04.02.01 | Precedence metric enforces |
| **Coverage gaps** | Edge cases untested | 1,024 synthetic cases cover all paths |

---

## Critical Success Factors

### 5 Pillars for Success

1. **Schema-first** 🏗️
   - BAML `ControllerTrace` finalized before metric work
   - Single source of truth for output contract

2. **Hard gates first** 🚪
   - Schema/enum/null violations = 0.0 immediately
   - No fuzzy scoring of broken outputs

3. **Rule separation** 🎯
   - Planner discerns (r01-r04)
   - Controller enforces (s01-s05)
   - Clear ownership

4. **Deterministic fixtures** 📋
   - FixtureSpecs define exact expected behavior
   - Known ground truth for every scenario

5. **Adversarial coverage** 🛡️
   - Enum traps, schema probes, rule conflicts
   - Test the failure modes explicitly

---


## Appendix: Metric Layer Breakdown

### Layer 1: Hard Gates (0.0 if fails)
```python
def schema_gate(prediction: str) -> bool:
    try:
        parse_json_to_type(prediction, ControllerTrace)
        return True
    except:
        return False  # → 0.0 score
```

### Layer 2: Rule Accuracy (Weighted)
```python
trigger_score = 0.6 * TriggerRuleAccuracy + 0.4 * RulePrecedence
# Both must be >0.9 to pass
```

### Layer 3: Quality (Weighted)
```python
quality_score = 0.7 * TraceAlignment + 0.3 * ResponseQuality
# Must be >0.8 to pass
```

### Final Score
```
final = 0.4 * rule_score + 0.6 * quality_score
pass iff final > 0.75
```

---

## Appendix: Sample Test Fixture

```yaml
spec_id: "fixture.ctrl.001"
scenario: "Linear ProductDiscovery → CatalogSearch"

input_turns:
  - "I need a comfy sweater"
  - "earthy tones please"
  - "she likes trekking"

expected_trace:
  turn_0: needs_clarification (2 slots)
  turn_1: needs_clarification (3 slots)
  turn_2: complete → Prepare_ProductCatalogSearch

rule_expectations:
  turn_0: {r01.03: true, r02: false, r04: false}
  turn_1: {r01.03: true, r02: false, r04: false}
  turn_2: {r01.03: false, r02: false, r04.02.01: true}
```

---

