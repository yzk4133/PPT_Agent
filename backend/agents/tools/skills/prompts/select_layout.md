---
skill_id: select_layout
name: Select Slide Layout Skill
version: 1.0.0
category: design
tags: [layout, design, slides, visual]
description: Decision framework for selecting appropriate PowerPoint slide layouts
author: MultiAgentPPT
enabled: true
---

# SelectSlideLayoutSkill - Layout Selection Framework

## Overview
This Skill provides a decision framework for choosing the most appropriate slide layout based on content type, media elements, and visual hierarchy.

## When to Use
- Creating new slides in a presentation
- Determining visual structure for content
- Optimizing slide readability and impact

## PowerPoint Layout Types

| Layout ID | Name | Best For |
|-----------|------|----------|
| 0 | Title | Opening slides, section dividers |
| 1 | Title and Content | Standard content slides |
| 2 | Section Header | Section dividers, transitions |
| 3 | Two Content | Side-by-side comparisons |
| 4 | Comparison | Pros/cons, before/after |
| 5 | Title Only | Full-screen impact, quotes |
| 6 | Blank | Custom designs, image-heavy |

## Decision Tree

### 1. Title Page
**Use: Title (0)**
- Presentation opening
- Major section divider
- Thank you/closing slide

**Characteristics:**
- Centered title
- Optional subtitle
- Minimal content

### 2. Table of Contents
**Use: Title and Content (1)**
- Agenda/overview
- List of topics
- Navigation slide

### 3. Section Header
**Use: Section Header (2)**
- Beginning of new section
- Chapter dividers
- Transition slides

### 4. Content + Image
**Use: Title and Content (1)**
- Main point with supporting visual
- Concept explanation with diagram
- Process description with illustration

**When to use Two Content (3) instead:**
- Need to balance text and image equally
- Image is wide/landscape format
- Text needs more space than subtitle provides

### 5. Content + Chart
**Use: Title and Content (1)**
- Data visualization
- Charts and graphs as main focus
- Statistics with supporting points

### 6. Image + Image (Comparison)
**Use: Two Content (3) or Comparison (4)**
- Before/after comparisons
- Side-by-side product comparison
- Pros/cons layout

**Use Comparison (4) when:**
- Direct comparison is needed
- Two distinct options being evaluated
- Visual symmetry is important

### 7. Text Only (Bullet Points)
**Use: Title and Content (1)**
- Standard bullet points
- Key takeaways
- Process steps
- 3-5 bullet points

**Use Two Content (3) when:**
- More than 5 bullet points
- Can group into two categories
- Need visual separation

### 8. Quote or Highlight
**Use: Title Only (5)**
- Inspirational quote
- Key statistic
- Impact statement
- Minimal text, maximum emphasis

### 9. Custom Layout
**Use: Blank (6)**
- Image dominates slide
- Custom positioning needed
- Infographic-style layout
- Multiple overlapping elements

## Content-to-Layout Mapping

| Content Type | Has Image | Has Chart | Bullet Count | Recommended Layout |
|--------------|-----------|-----------|--------------|-------------------|
| Title Page | No | No | 0 | Title (0) |
| Section Header | No | No | 0 | Section Header (2) |
| TOC | No | No | 5-10 | Title and Content (1) |
| Quote | No | No | 1 | Title Only (5) |
| Standard Content | No | No | 3-5 | Title and Content (1) |
| Long Content | No | No | 6+ | Two Content (3) |
| Content + Image | Yes | No | 1-3 | Title and Content (1) |
| Content + Image | Yes | No | 4+ | Two Content (3) |
| Content + Chart | No | Yes | 1-5 | Title and Content (1) |
| Chart + Image | Yes | Yes | - | Two Content (3) |
| Comparison | Optional | Optional | - | Comparison (4) |
| Image-Dominant | Yes | No | 0-2 | Blank (6) |

## Best Practices

### Readability
- **Maximum 5-7 bullets per slide**
- **Maximum 6-8 words per bullet**
- **Font size: minimum 24pt** for body text
- **Contrast**: ensure text is readable against background

### Visual Hierarchy
1. **Title** - Largest, most prominent
2. **Subtitle** (optional) - Medium size
3. **Content** - Body text size
4. **Footnotes** (optional) - Smallest

### Balance
- **Avoid overcrowding**: Leave white space
- **Align elements**: Use grid alignment
- **Consistent positioning**: Similar elements in same place

### Media Placement
- **Images**: Place on right for LTR languages (reading flow)
- **Charts**: Center or right-aligned
- **Logo**: Bottom right corner (small)

## Common Mistakes to Avoid

❌ Using Title layout for regular content slides
❌ Putting 10+ bullet points on one slide
❌ Using Comparison layout for single item
❌ Text covering images
❌ Inconsistent layout usage in same section

## Examples

### Example 1: Standard Bullet Slide
```
Title: "Key Benefits"
Layout: Title and Content (1)
Content:
- Increased efficiency by 40%
- Reduced costs significantly
- Improved user satisfaction
- Faster time to market
```

### Example 2: Comparison Slide
```
Title: "Product Comparison"
Layout: Comparison (4)
Left Content: "Product A"
- Lower cost
- Easier setup
Right Content: "Product B"
- More features
- Better scalability
```

### Example 3: Image-Dominant Slide
```
Title: "Market Growth"
Layout: Blank (6)
Elements:
- Large chart image centered
- Small caption below
- Logo in bottom right
```
