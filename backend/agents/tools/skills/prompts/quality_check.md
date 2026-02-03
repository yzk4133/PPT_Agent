---
skill_id: quality_check
name: Quality Check Skill
version: 1.0.0
category: quality
tags: [quality, validation, review, standards]
description: Comprehensive quality assessment framework for presentation content
author: MultiAgentPPT
enabled: true
---

# QualityCheckSkill - Content Quality Assessment

## Overview
This Skill provides a systematic framework for evaluating the quality of presentation content across multiple dimensions including completeness, logic, clarity, and visual design.

## When to Use
- Reviewing generated content before finalizing
- Validating content meets requirements
- Ensuring consistency across presentation
- Identifying areas needing improvement

## Quality Dimensions

### 1. Completeness
**Checks:**
- ✓ All required topics are covered
- ✓ Introduction, body, and conclusion present
- ✓ Key points elaborated with sufficient detail
- ✓ Data and statistics supported with sources
- ✓ No abrupt endings or missing transitions

**Assessment:**
- **Excellent**: All topics covered with depth
- **Good**: Most topics covered, minor gaps
- **Fair**: Significant gaps in coverage
- **Poor**: Major topics missing

### 2. Logic & Structure
**Checks:**
- ✓ Clear flow and progression
- ✓ Ideas connected logically
- ✓ No contradictions
- ✓ Arguments well-supported
- ✓ Transitions between sections smooth

**Assessment:**
- **Excellent**: Seamless flow, compelling narrative
- **Good**: Logical flow, minor disconnects
- **Fair**: Some logical gaps
- **Poor**: Confusing or contradictory

### 3. Clarity & Expression
**Checks:**
- ✓ Language appropriate for audience
- ✓ Jargon explained or avoided
- ✓ Sentences clear and concise
- ✓ Active voice preferred
- ✓ No ambiguous statements

**Assessment:**
- **Excellent**: Crystal clear, engaging
- **Good**: Generally clear, minor confusion points
- **Fair**: Some unclear sections
- **Poor**: Difficult to understand

### 4. Visual & Layout
**Checks:**
- ✓ Appropriate layouts selected
- ✓ Text readable (font size, contrast)
- ✓ Images relevant and high-quality
- ✓ Consistent formatting
- ✓ Not overcrowded

**Assessment:**
- **Excellent**: Professional, visually appealing
- **Good**: Clean, mostly consistent
- **Fair**: Some layout issues
- **Poor**: Hard to read or unprofessional

### 5. Accuracy & Credibility
**Checks:**
- ✓ Facts and data accurate
- ✓ Sources cited properly
- ✓ Statistics current
- ✓ No misleading claims
- ✓ Expert opinions attributed

**Assessment:**
- **Excellent**: All claims verified and cited
- **Good**: Most claims supported
- **Fair**: Some unsupported claims
- **Poor**: Multiple inaccuracies

## Quality Report Format

```json
{
  "presentation_title": "Title",
  "overall_quality": "Good",
  "overall_score": 7.5,
  "dimension_scores": {
    "completeness": 8.0,
    "logic_structure": 7.0,
    "clarity_expression": 8.0,
    "visual_layout": 7.0,
    "accuracy_credibility": 7.5
  },
  "strengths": [
    "Comprehensive coverage of topic",
    "Clear language throughout",
    "Good use of supporting data"
  ],
  "weaknesses": [
    "Some transitions between sections abrupt",
    "Inconsistent bullet point formatting",
    "Missing source citations in slide 5"
  ],
  "recommendations": [
    "Add transition sentences between major sections",
    "Standardize bullet point format across all slides",
    "Add source citations for all statistics",
    "Consider adding visual elements to slide 3"
  ],
  "priority_issues": [
    {
      "issue": "Missing conclusion slide",
      "severity": "high",
      "location": "End of presentation",
      "suggestion": "Add summary and call-to-action slide"
    }
  ]
}
```

## Common Quality Issues

### Content Issues

| Issue | Severity | Fix |
|-------|----------|-----|
| Missing introduction | High | Add title slide with overview |
| Abrupt ending | High | Add conclusion/summary slide |
| Unsupported claims | Medium | Add sources or data |
| Too much text | Medium | Split into multiple slides |
| Unclear terminology | Low | Add definitions or glossary |

### Visual Issues

| Issue | Severity | Fix |
|-------|----------|-----|
| Text too small | High | Increase font size (>24pt) |
| Poor contrast | High | Change colors for readability |
| Inconsistent fonts | Medium | Use template styles |
| Low-quality images | Medium | Replace with high-res versions |
| Overcrowded slides | Low | Remove or redistribute content |

### Logic Issues

| Issue | Severity | Fix |
|-------|----------|-----|
| Contradictory statements | High | Resolve or acknowledge |
| Missing transitions | Medium | Add transition sentences |
| Unclear flow | Medium | Reorder or add signposts |
| Weak arguments | Low | Strengthen with evidence |

## Assessment Checklist

Use this checklist for systematic quality assessment:

```
Content Structure:
□ Title slide present
□ Agenda/overview included
□ Main content organized logically
□ Each section has clear purpose
□ Conclusion/summary present
□ Call-to-action included (if applicable)

Content Quality:
□ Topic covered comprehensively
□ Key points elaborated
□ Examples and illustrations included
□ Data and statistics support claims
□ Sources cited properly

Visual Design:
□ Appropriate layouts used
□ Text readable (size, contrast)
□ Consistent formatting
□ High-quality images
□ Not overcrowded

Language & Tone:
□ Clear and concise
□ Appropriate for audience
□ Active voice preferred
□ No grammatical errors
□ Consistent terminology

Accuracy:
□ Facts verified
□ Statistics current
□ No misleading claims
□ Expert opinions attributed
□ No contradictions
```

## Quality Score Calculation

```
Overall Score = (Completeness × 0.25) +
                (Logic × 0.25) +
                (Clarity × 0.20) +
                (Visual × 0.15) +
                (Accuracy × 0.15)

Rating Scale:
9.0 - 10.0: Excellent (Ready to deliver)
7.5 - 8.9:  Good (Minor improvements recommended)
6.0 - 7.4:  Fair (Improvements needed)
< 6.0:      Poor (Major revision required)
```

## Best Practices

### For Reviewers
1. **Be Specific**: Point to exact slides/sections with issues
2. **Prioritize**: Highlight critical issues vs. nice-to-haves
3. **Provide Solutions**: Suggest concrete improvements
4. **Be Constructive**: Frame feedback positively
5. **Consider Context**: Assess against intended audience

### For Content Creators
1. **Self-Review**: Use checklist before submitting
2. **Get Feedback**: Multiple reviewers catch different issues
3. **Iterate**: Quality improves with multiple passes
4. **Document**: Track changes and improvements
5. **Learn**: Note common mistakes to avoid

## Integration with Other Skills

Use with:
- **ResearchTopicSkill**: Ensure research findings are accurately presented
- **SelectSlideLayoutSkill**: Verify layout choices are appropriate
- **OptimizeContentSkill**: Apply optimization recommendations
