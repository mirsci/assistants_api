---
marp: true
theme: default
class: invert
paginate: true
footer: "Hybrid-AI Shopping Assistant Controller | DeepEval Implementation Roadmap"
---

# DeepEval Implementation Roadmap
## Shopping Controller Adapter

**Building a Production-Ready Evaluation Pipeline**

---

## Executive Summary

### The Problem
- **Current:** Manual testing, ad-hoc prompts, no systematic quality measurement
- **Risk:** Regressions slip to production; quality degrades silently
- **Impact:** Customer escalations, lost cashback opportunities, broken workflows

### The Solution
- **Automated multi-layer evaluation** with DeepEval, DSPy, and FixtureSpec
- **1,024+ synthetic test scenarios** covering all customer paths
- **CI/CD gates** preventing regressions before deployment

### The Payoff
- **18-25 days** to production-ready system
- **~$15-25K** one-time investment
- **40 hours/month** QA savings ongoing

---

## Business Impact by Stakeholder

| Role | Value Delivered |
|------|-----------------|
| **Product** | Confidence across 1,000+ scenarios |
| **Engineering** | Automated regression detection |
| **Operations** | Quantified quality metrics for release go/no-go |
| **Business** | Reduced customer escalations |
| **Finance** | ROI: 6-12 months, breaks even after 1 incident prevention |

---

## Investment Overview

| Metric | Value |
|--------|-------|
| **Duration** | 18-25 days |
| **Output** | Production-ready evaluation suite with CI/CD |
| **Coverage** | 1,024+ synthetic + adversarial cases |
| **Ongoing Cost** | $5-10/day for judge LLM calls (GPT-4o-mini) |
| **Monthly Savings** | ~$2-3K (manual QA elimination) |

---

# Phase 1: Schema Contract Definition
## Foundation for All Evaluation

**Duration:** 1-2 days | **Risk if Skipped:** 🔴 **HIGH**

### Without Schema Contract
- ❌ Can't distinguish broken model vs policy violation vs quality issue
- ❌ Invalid JSON wastes judge LLM calls
- ❌ Enum drift undetected ("Prepare MerchantSearch" becomes prose)
- ❌ Silent failures in downstream systems

### With Schema Contract
- ✅ Fail-fast detection (<1 second per violation)
- ✅ Engineering clarity on output shape
- ✅ BAML schema = code versioning
- ✅ Downstream automation enabled

---

## Phase 1: Implementation

**BAML Schema Definition**
```baml
class ControllerTrace {
  trace ControllerTraceInner
  next_action NextAction           # Must be enum, never paraphrased
  shopper_response string          # Never null
  blocking_reason string?
}

enum NextAction {
  Ask_ProductDiscovery_clarification
  Prepare_MerchantSearch
  Prepare_ProductCatalogSearch
}
```

**Hard Gates**
- Schema compliance: 0.0 if invalid JSON
- Enum compliance: 0.0 if not valid enum
- Non-null gate: 0.0 if shopper_response missing

---

# Phase 2: Rule Evaluation Metrics
## Validating Business Logic

**Duration:** 3-4 days | **Risk if Skipped:** 🔴 **HIGH**

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

**Duration:** 2-3 days | **Risk if Skipped:** 🟡 **MEDIUM**

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

**Duration:** 3-4 days | **Risk if Skipped:** 🟡 **MEDIUM**

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
## Single Release Decision Point

**Duration:** 2-3 days | **Risk if Skipped:** 🟢 **LOW**

### Three-Layer Evaluation
```
Layer 1 (Hard Gates)        → Must be 100%
  Schema valid? Enum valid? Non-null?
           ↓
Layer 2 (Rule Accuracy)     → Target >90%
  Do rules trigger correctly?
           ↓
Layer 3 (Quality)           → Target >80%
  Trace alignment? Response quality?
           ↓
FINAL SCORE (0.0-1.0)       → Release gate: 0.75+
```

### Why Single Metric?
- ✅ One threshold for go/no-go decisions
- ✅ Weighted priorities visible
- ✅ Failure analysis built-in
- ✅ Historical trending enabled

---

# Phase 6: Test Data Generation
## 1,024+ Synthetic Scenarios

**Duration:** 3-4 days | **Risk if Skipped:** 🔴 **HIGH**

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
- ✅ Generated: <5 minutes, systematic, reproducible

### Adversarial Coverage
- Enum traps ("prepare merchant" instead of enum)
- Schema probes (request specific JSON fields)
- Rule conflicts (r02 + r04.02.01 simultaneously)

---

# Phase 7: Prompt Optimization
## Learnable Prompt Improvement

**Duration:** 2-3 days | **Risk if Skipped:** 🟢 **LOW**

### Traditional Loop (❌ Slow)
1. Run eval → see failures
2. Manually tweak prompt
3. Re-run eval → hope it improves
4. Repeat 5-10x per month

### DSPy Loop (✅ Fast)
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

**Duration:** 1-2 days | **Risk if Skipped:** 🔴 **HIGH**

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

### GitHub Actions Workflow
```yaml
on:
  push:
    paths:
      - 'docs/planning-domain/llm-evals/**'
      
steps:
  - Run DeepEval tests (controller_adapter metric)
  - Pass rate must be >0.75 to merge
  - Artifact trending for dashboard
```

---

## Implementation Timeline

| Phase | Duration | Key Output | Status |
|-------|----------|-----------|--------|
| **1. Schema** | 1-2 days | BAML schema + hard gates | 📋 Ready |
| **2. Rules** | 3-4 days | Trigger + precedence metrics | 📋 Ready |
| **3. Trace** | 2-3 days | FixtureSpec + alignment | 📋 Ready |
| **4. Multi-Turn** | 3-4 days | ConversationalGEval | 📋 Ready |
| **5. Composite** | 2-3 days | ControllerAdapterMetric | 📋 Ready |
| **6. DataGen** | 3-4 days | 1,024 synthetic test cases | 📋 Ready |
| **7. Optimization** | 2-3 days | MIPROv2 optimization | 📋 Ready |
| **8. CI/CD** | 1-2 days | GitHub Actions workflow | 📋 Ready |

**Total: 18-25 business days**

---

## Financial Analysis

### Investment Breakdown
| Category | One-Time | Monthly |
|----------|----------|---------|
| Engineering | $15-25K | — |
| Judge LLM API | — | $100-300 |
| CI compute | — | $50-100 |
| **Total** | **$15-25K** | **~$300/mo** |

### Expected Returns
| Benefit | Value |
|---------|-------|
| Manual QA elimination | ~40 hrs/month (~$2-3K) |
| Production incident prevention | 1-2 per quarter (~$10K+ each) |
| Faster iteration cycles | 10-20% velocity increase |
| Reduced stakeholder alignment | ~5 hrs/week saved |

### Break-Even
- **6-12 months** via QA savings
- **Immediate** after preventing one incident

---

## Risk Mitigation

### What We're Protecting Against

| Risk | Consequence | Mitigation |
|------|-------------|-----------|
| **Silent rule drift** | Wrong decisions in production | Automated regression detection |
| **Enum backsliding** | Model outputs prose instead of enum | Hard gate (0.0 score immediately) |
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

## Next Steps

### Immediate (Week 1)
- [ ] Finalize BAML `ControllerTrace` schema
- [ ] Validate with live inference server
- [ ] Create hard gate implementation

### Short-term (Weeks 2-3)
- [ ] Build rule metrics (TriggerRuleAccuracy, RulePrecedence)
- [ ] Create initial FixtureSpecs (manual authoring)
- [ ] Test with existing test cases

### Medium-term (Weeks 4-5)
- [ ] Attribute grid definition (1,024 combinations)
- [ ] Fixture generation automation
- [ ] Composite metric integration

### Long-term (Weeks 6+)
- [ ] DSPy MIPROv2 optimization
- [ ] GitHub Actions CI/CD pipeline
- [ ] Dashboard + trend visualization

---

## Questions?

### Contact & Resources
- **DeepEval Docs:** https://docs.deepeval.ai
- **BAML Docs:** https://www.boundaryml.com/docs
- **Roadmap Spec:** `/docs/planning-domain/llm-evals/llmeval.ctrl.007-rules-based-controller.md`

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

## Appendix: ROI Scenarios

### Conservative (Low Incident Prevention)
- QA savings: 40 hrs/month = $2K/month
- Incidents prevented: 1 per year = $5K value
- **Break-even: 8-10 months** via QA + incident

### Realistic (One Incident Prevented)
- QA savings: $2K/month
- Incident value: $15-20K (customer escalations, fixes, QA)
- **Break-even: Immediate to 3 months**

### Optimistic (Iteration Velocity)
- QA savings: $2-3K/month
- Incident prevention: 1-2 per quarter
- Iteration velocity: 10-20% faster (dev time savings)
- **ROI: 200-300% annually**

