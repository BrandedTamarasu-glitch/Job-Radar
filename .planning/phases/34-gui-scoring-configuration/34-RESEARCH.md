# Phase 34: GUI Scoring Configuration - Research

**Researched:** 2026-02-13
**Domain:** CustomTkinter GUI programming with live preview, validation, and state management
**Confidence:** HIGH

## Summary

This phase delivers GUI controls for customizing job scoring configuration through sliders (6 component weights) and a dropdown (staffing firm preference). The research confirms CustomTkinter provides all necessary widgets (CTkSlider, CTkOptionMenu) with robust callback systems for real-time updates. The existing codebase already demonstrates validation patterns, collapsible sections can be implemented via CTkCollapsiblePanel or custom implementation, and state persistence follows the existing profile_manager.save_profile() pattern.

The standard approach is to use CTkSlider with command callbacks for real-time updates, CTkOptionMenu for the staffing preference dropdown, and CTkLabel for live preview display. Validation should follow the existing pattern: live warnings during editing (non-blocking) plus save-time enforcement (blocking). The normalize button provides UX sugar by proportionally adjusting weights to sum to 1.0.

**Primary recommendation:** Build scoring configuration as a collapsible section within the existing Settings tab using CTkSlider widgets (0.0-1.0 range with number_of_steps), CTkOptionMenu for staffing preference, and a side-by-side layout (sliders left, live preview right) for immediate feedback on score impact.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| customtkinter | Latest (5.2.x) | Modern Tkinter UI framework | Already used throughout job_radar.gui, provides CTkSlider, CTkOptionMenu, themed widgets |
| CTkToolTip | Latest | Tooltip widget for help icons | Official CustomTkinter tooltip library, pip-installable, supports dynamic message updates |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| CTkCollapsiblePanel | Latest | Collapsible section widget | OPTIONAL - can implement collapse/expand manually if avoiding external dependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CTkCollapsiblePanel | Manual toggle implementation | CTkCollapsiblePanel is cleaner but adds dependency; manual toggle is 20-30 LOC with grid_forget() |
| CTkToolTip | Manual Toplevel tooltip | CTkToolTip provides transparency, rounded corners, follow-cursor; manual requires 40+ LOC |

**Installation:**
```bash
pip install customtkinter CTkToolTip
# CTkCollapsiblePanel: copy from GitHub or implement manually
```

## Architecture Patterns

### Recommended Component Structure
```
Settings Tab (existing)
└── CTkScrollableFrame (existing)
    └── CollapsibleScoringSection (new)
        ├── Header with expand/collapse control
        └── Content Frame (shown/hidden)
            ├── Left Panel: Sliders
            │   ├── Slider Group 1: Skills & Fit
            │   │   ├── CTkSlider: skill_match (0.0-1.0)
            │   │   ├── CTkSlider: title_relevance
            │   │   ├── CTkSlider: seniority
            │   │   └── CTkSlider: domain
            │   ├── Slider Group 2: Context
            │   │   ├── CTkSlider: location
            │   │   └── CTkSlider: response_likelihood
            │   ├── CTkOptionMenu: staffing_preference
            │   └── Action Buttons (Normalize, Reset)
            └── Right Panel: Live Preview
                ├── Sample job characteristics (hardcoded)
                ├── Component score breakdown
                └── Before/after overall score display
```

### Pattern 1: Real-Time Slider Update with Live Preview
**What:** CTkSlider command callback triggers immediate preview recalculation without debouncing
**When to use:** User expects instant visual feedback; calculations are lightweight (< 10ms)
**Example:**
```python
# Source: https://customtkinter.tomschimansky.com/documentation/widgets/slider/
def slider_callback(value):
    # Update label showing value + percentage
    label.configure(text=f"{value:.2f} ({value*100:.0f}%)")
    # Recalculate live preview immediately
    update_live_preview()

slider = ctk.CTkSlider(
    parent,
    from_=0.0,
    to=1.0,
    number_of_steps=20,  # 0.05 increments
    command=slider_callback
)
```

### Pattern 2: Sum-to-1.0 Validation with Live Warning
**What:** Non-blocking validation during editing shows warning banner; blocking validation prevents save
**When to use:** User needs guidance but shouldn't be blocked from experimenting
**Example:**
```python
# Live warning (non-blocking)
def check_sum_constraint():
    total = sum(slider.get() for slider in weight_sliders.values())
    if abs(total - 1.0) > 0.001:
        warning_label.configure(
            text=f"Weights sum to {total:.3f} (must be 1.0). Use Normalize button to fix.",
            text_color="orange"
        )
    else:
        warning_label.configure(text="")

# Save validation (blocking)
def save_scoring_config():
    total = sum(slider.get() for slider in weight_sliders.values())
    if abs(total - 1.0) > 0.001:
        messagebox.showerror("Invalid Configuration",
            f"Weights must sum to 1.0 (currently {total:.3f})")
        return False
    # Proceed with save...
```

### Pattern 3: Normalize Button (Proportional Adjustment)
**What:** Proportionally adjust all weights to sum to 1.0 while preserving relative ratios
**When to use:** User has rough weights but sum != 1.0; avoids manual math
**Example:**
```python
def normalize_weights():
    # Get current values
    weights = {k: slider.get() for k, slider in weight_sliders.items()}
    total = sum(weights.values())

    if total == 0:
        # Equal distribution fallback
        normalized = {k: 1.0/len(weights) for k in weights}
    else:
        # Proportional scaling
        normalized = {k: v/total for k, v in weights.items()}

    # Update sliders
    for component, value in normalized.items():
        weight_sliders[component].set(value)

    # Trigger preview update
    update_live_preview()
```

### Pattern 4: Collapsible Section with State Persistence
**What:** Expand/collapse control with last state saved to config or localStorage-like mechanism
**When to use:** Settings tab contains multiple sections; user preference should persist
**Example:**
```python
# Option A: CTkCollapsiblePanel (if using external library)
panel = CTkCollapsiblePanel(parent, title="Scoring Configuration")
# Add widgets to panel._content_frame
label = ctk.CTkLabel(panel._content_frame, text="Weights")
label.pack()

# Option B: Manual implementation (no external dependency)
class CollapsibleSection(ctk.CTkFrame):
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, **kwargs)

        # Header button
        self.header = ctk.CTkButton(
            self, text=f"▼ {title}", command=self.toggle,
            anchor="w", fg_color="transparent"
        )
        self.header.pack(fill="x")

        # Content frame
        self.content = ctk.CTkFrame(self)
        self.content.pack(fill="both", expand=True)
        self.is_expanded = True

    def toggle(self):
        if self.is_expanded:
            self.content.pack_forget()
            self.header.configure(text=self.header.cget("text").replace("▼", "▶"))
        else:
            self.content.pack(fill="both", expand=True)
            self.header.configure(text=self.header.cget("text").replace("▶", "▼"))
        self.is_expanded = not self.is_expanded
```

### Pattern 5: Live Preview with Hardcoded Sample Job
**What:** Use fixed job characteristics to demonstrate scoring impact; recalculate on every slider change
**When to use:** Preview should be predictable and demonstrate all components
**Example:**
```python
# Hardcoded sample job matching all scoring dimensions
SAMPLE_JOB = {
    "title": "Senior Python Developer",
    "company": "TechCorp",
    "description": "Python, Django, AWS, 5+ years, remote options",
    "location": "Remote",
    "compensation": "$120,000",
    "posted_date": "2 days ago"
}

def update_live_preview():
    # Get current weights
    weights = {k: slider.get() for k, slider in weight_sliders.items()}

    # Calculate component scores (simplified from scoring.py)
    components = {
        "skill_match": 4.5,      # High match
        "title_relevance": 4.0,  # Strong match
        "seniority": 3.8,        # Good fit
        "location": 5.0,         # Perfect (remote)
        "domain": 3.5,           # Relevant
        "response_likelihood": 3.2  # Average
    }

    # Calculate weighted score
    score = sum(components[k] * weights[k] for k in components)

    # Display breakdown
    preview_text = "Sample Job Score:\n"
    for component, comp_score in components.items():
        weighted = comp_score * weights[component]
        preview_text += f"  {component}: {comp_score} × {weights[component]:.2f} = {weighted:.2f}\n"
    preview_text += f"\nOverall: {score:.2f} / 5.0"

    preview_label.configure(text=preview_text)
```

### Anti-Patterns to Avoid
- **Debouncing slider callbacks:** Users expect instant feedback; scoring calculation is fast enough for real-time updates
- **Mixing validation styles:** Don't use messageboxes for live validation (too disruptive); use inline labels with text_color="orange"
- **Blocking save with auto-fix:** Don't silently normalize on save; user should explicitly click Normalize button (transparency)
- **Global state for slider values:** Use instance variables in class-based widgets to avoid conflicts

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tooltip widget | Custom Toplevel with position calculation | CTkToolTip library | Handles edge detection, transparency, rounded corners, follow-cursor, theme integration |
| Collapsible panel | Custom show/hide logic | CTkCollapsiblePanel (or 30 LOC pattern) | Handles animation, state tracking, accessibility (keyboard nav) |
| Weight normalization math | Manual proportional calculation | Standard pattern (value/sum) | Edge cases: all zeros, negative values, floating point precision |
| Live preview debouncing | Custom timer + cancel logic | No debouncing needed | Scoring calculation is <10ms; instant feedback is better UX |
| Slider value formatting | String manipulation | f-string with format specifiers | f"{value:.2f} ({value*100:.0f}%)" handles precision + percentage |

**Key insight:** CustomTkinter's widget ecosystem provides production-ready solutions for common UI patterns. Reinventing tooltip positioning, collapsible animations, or theme integration introduces bugs and maintenance burden. Use official widgets or established patterns.

## Common Pitfalls

### Pitfall 1: Slider number_of_steps Confusion
**What goes wrong:** Slider appears to move smoothly but produces arbitrary decimal values (e.g., 0.247), confusing users
**Why it happens:** number_of_steps parameter is often misunderstood; omitting it creates continuous slider with float precision
**How to avoid:** Explicitly set number_of_steps based on desired increment: `number_of_steps = int((to - from_) / increment)`. For 0.0-1.0 range with 0.05 increments: `number_of_steps=20`
**Warning signs:** Users report "can't get exact values" or weights sum to 0.998 instead of 1.0

### Pitfall 2: Validation Blocking User Exploration
**What goes wrong:** Save button is disabled or greyed out whenever sum != 1.0, frustrating users experimenting with weights
**Why it happens:** Conflating "validation" with "blocking"; user needs to try combinations before normalizing
**How to avoid:** Use two-tier validation: (1) Live warning (orange text, non-blocking), (2) Save enforcement (messagebox on save click). Provide Normalize button as easy fix.
**Warning signs:** User complaints about "can't save" or "stuck in invalid state"

### Pitfall 3: Live Preview Using Real Search Results
**What goes wrong:** Preview tries to recalculate scores for user's actual search results, causing performance issues or empty preview if no search run yet
**Why it happens:** Desire for "realistic" preview leads to coupling with search state
**How to avoid:** Use hardcoded sample job with known characteristics. Document that preview is "representative example, not actual results." Keep preview fast and predictable.
**Warning signs:** Preview is slow, blank, or shows stale data from previous search

### Pitfall 4: Forgetting staffing_preference is Post-Scoring
**What goes wrong:** Implementing staffing preference as a weight component (7th slider), violating the design constraint that weights must sum to 1.0
**Why it happens:** staffing_preference feels like a weight; developer doesn't read scoring.py implementation showing it's applied AFTER weighted sum
**How to avoid:** Use CTkOptionMenu with 3 values ("boost", "neutral", "penalize"), NOT a slider. Document that this is a post-scoring adjustment (+0.5, 0, -1.0), not a weight.
**Warning signs:** Weights sum validation fails, or scoring.py throws errors

### Pitfall 5: Not Handling Minimum Weight Constraint
**What goes wrong:** User sets a weight to 0.0, violating the 0.05 minimum constraint from Phase 33 design
**Why it happens:** Slider from_=0.0 allows zero values; validation only checks sum to 1.0, not individual minimums
**How to avoid:** Set slider from_=0.05 (enforced at widget level), OR validate on save that all weights >= 0.05. Display error message referencing the constraint.
**Warning signs:** Profile save fails with cryptic error; users report "can't disable a scoring component"

### Pitfall 6: State Persistence Confusion
**What goes wrong:** Collapsible section expand/collapse state is not saved, resetting to default every launch
**Why it happens:** Assuming CustomTkinter widgets auto-save state; no mechanism implemented
**How to avoid:**
- Option A: Store in config.json (add "scoring_section_expanded" key)
- Option B: Simple heuristic (expanded on first visit if scoring_weights == defaults, collapsed if customized)
- Option C: Don't persist (acceptable UX; user re-expands if needed)
**Warning signs:** User feedback about "section keeps collapsing" or "why is this always open?"

## Code Examples

Verified patterns from official sources:

### CTkSlider with Real-Time Callback
```python
# Source: https://customtkinter.tomschimansky.com/documentation/widgets/slider/
import customtkinter as ctk

def weight_changed(component_name, value):
    """Called whenever a weight slider moves."""
    # Update display label
    labels[component_name].configure(text=f"{value:.2f} ({value*100:.0f}%)")

    # Check sum constraint (live warning, non-blocking)
    check_sum_validation()

    # Update live preview
    recalculate_preview()

# Create slider with 0.05 increments (20 steps from 0.05 to 1.0)
skill_slider = ctk.CTkSlider(
    parent,
    from_=0.05,           # Minimum 0.05 per Phase 33 constraint
    to=1.0,
    number_of_steps=19,   # (1.0 - 0.05) / 0.05 = 19 steps
    command=lambda val: weight_changed("skill_match", val)
)
skill_slider.set(0.25)  # Default weight
```

### CTkOptionMenu for Staffing Preference
```python
# Source: https://customtkinter.tomschimansky.com/documentation/widgets/optionmenu/
import customtkinter as ctk

def staffing_pref_changed(choice):
    """Called when staffing preference dropdown changes."""
    print(f"Staffing preference: {choice}")
    recalculate_preview()  # Update live preview with new preference

staffing_menu = ctk.CTkOptionMenu(
    parent,
    values=["boost", "neutral", "penalize"],
    command=staffing_pref_changed
)
staffing_menu.set("neutral")  # Default from Phase 33
```

### CTkToolTip for Help Icons
```python
# Source: https://pypi.org/project/CTkToolTip/
from CTkToolTip import CTkToolTip
import customtkinter as ctk

# Create help icon button
help_button = ctk.CTkButton(
    parent,
    text="?",
    width=25,
    height=25,
    fg_color="transparent",
    text_color="gray",
    hover=False
)
help_button.pack(side="left", padx=5)

# Attach tooltip
CTkToolTip(
    help_button,
    message="Skill match weight determines how much emphasis is placed on matching your core skills vs required skills in the job description.",
    delay=0.3,
    alpha=0.95
)
```

### Live Preview Panel
```python
# Pattern: Side-by-side layout with live updates
import customtkinter as ctk

class ScoringConfigSection(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Configure grid: left=sliders, right=preview
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Left panel: Sliders
        slider_frame = ctk.CTkFrame(self)
        slider_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Right panel: Live preview
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Adjust sliders to see score impact →",
            justify="left",
            anchor="nw"
        )
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)

    def update_preview(self, weights, staffing_pref):
        """Recalculate and display sample job score."""
        # Sample job (hardcoded)
        sample_components = {
            "skill_match": 4.5,
            "title_relevance": 4.0,
            "seniority": 3.8,
            "location": 5.0,
            "domain": 3.5,
            "response_likelihood": 3.2
        }

        # Weighted calculation
        score = sum(sample_components[k] * weights.get(k, 0) for k in sample_components)

        # Staffing adjustment (if applicable)
        if staffing_pref == "boost":
            score = min(5.0, score + 0.5)
            staffing_note = " (+0.5 boost)"
        elif staffing_pref == "penalize":
            score = max(1.0, score - 1.0)
            staffing_note = " (-1.0 penalty)"
        else:
            staffing_note = ""

        # Format display
        preview_text = "Sample Job: Senior Python Developer\n\n"
        preview_text += "Component Scores:\n"
        for comp, comp_score in sample_components.items():
            weighted = comp_score * weights.get(comp, 0)
            preview_text += f"  {comp}: {comp_score:.1f} × {weights.get(comp, 0):.2f} = {weighted:.2f}\n"
        preview_text += f"\nOverall Score: {score:.2f}/5.0{staffing_note}"

        self.preview_label.configure(text=preview_text)
```

### Save Validation with Profile Manager Integration
```python
# Pattern: Validate then save using existing profile_manager
from job_radar.profile_manager import save_profile, load_profile
from job_radar.paths import get_data_dir

def save_scoring_configuration():
    """Validate weights and save to profile.json."""
    # Gather current slider values
    weights = {
        "skill_match": skill_slider.get(),
        "title_relevance": title_slider.get(),
        "seniority": seniority_slider.get(),
        "location": location_slider.get(),
        "domain": domain_slider.get(),
        "response_likelihood": response_slider.get(),
    }

    # Validation: Sum to 1.0
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        show_error(f"Weights must sum to 1.0 (currently {total:.3f})")
        return False

    # Validation: Minimum 0.05 per component
    for component, value in weights.items():
        if value < 0.05:
            show_error(f"{component} must be at least 0.05 (currently {value:.2f})")
            return False

    # Load current profile
    profile_path = get_data_dir() / "profile.json"
    profile = load_profile(profile_path)

    # Update scoring configuration
    profile["scoring_weights"] = weights
    profile["staffing_preference"] = staffing_menu.get()

    # Save via profile_manager (atomic write, backup, validation)
    save_profile(profile_path, profile)

    # Show success message
    show_success("Scoring configuration saved successfully!")
    return True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded scoring weights in scoring.py | User-configurable weights in profile v2 | Phase 33 (2026-02-13) | Users can customize; GUI must support profile schema v2 |
| No staffing firm preference | boost/neutral/penalize options | Phase 33 (2026-02-13) | GUI must provide dropdown, not slider (post-scoring adjustment) |
| CLI-only wizard for weight config | GUI + wizard both supported | Phase 34 (current) | Settings tab provides visual alternative to CLI |
| tkinter standard widgets | CustomTkinter modern widgets | App inception | Use CTk* widgets for consistency; follow existing patterns |

**Deprecated/outdated:**
- Manual tooltip implementation: Use CTkToolTip library (pip-installable, maintained)
- Debouncing slider callbacks: Not needed for fast calculations (< 10ms); instant feedback is better UX
- Blocking validation during editing: Use live warnings (non-blocking) + save enforcement (blocking)

## Open Questions

Things that couldn't be fully resolved:

1. **Slider increment granularity (0.01 vs 0.05 vs 0.10)**
   - What we know: User decision marks this as "Claude's Discretion"; smaller increments = more precision but harder to hit exact values
   - What's unclear: User preference between fine-grained control vs ease of use
   - Recommendation: Start with 0.05 increments (number_of_steps=19) as good balance; can adjust based on user feedback. Finer increments (0.01) make it harder to normalize manually.

2. **Category groupings for sliders (Skills/Fit/Response vs other)**
   - What we know: User decision marks this as "Claude's Discretion"; 6 components could be grouped multiple ways
   - What's unclear: Optimal cognitive grouping for users
   - Recommendation: Group by purpose — "Skills & Fit" (skill_match, title_relevance, seniority, domain) and "Context" (location, response_likelihood). This separates "what you can do" from "where/when/how likely."

3. **Error display pattern (banner vs inline vs toast)**
   - What we know: User decision marks this as "Claude's Discretion"; existing code uses inline labels (see SearchControls, ProfileForm)
   - What's unclear: Best pattern for Settings tab multi-field validation
   - Recommendation: Use inline warning label below sliders (consistent with SearchControls._score_error_label pattern) with text_color="orange" for live warnings, messagebox on save block for enforcement.

4. **Collapsible section state persistence mechanism**
   - What we know: User wants initial state "expanded on first visit, then remember user's last state"
   - What's unclear: Where to persist this state (config.json? profile.json? new settings file?)
   - Recommendation: Add "ui_preferences" top-level key to config.json with {"scoring_section_expanded": true/false}. Falls back to heuristic if not present: expanded if scoring_weights == defaults, collapsed if customized.

## Sources

### Primary (HIGH confidence)
- CustomTkinter CTkSlider documentation: https://customtkinter.tomschimansky.com/documentation/widgets/slider/
- CustomTkinter CTkOptionMenu documentation: https://customtkinter.tomschimansky.com/documentation/widgets/optionmenu/
- CustomTkinter GitHub Wiki - App structure: https://github.com/TomSchimansky/CustomTkinter/wiki/App-structure-and-layout
- CTkToolTip PyPI documentation: https://pypi.org/project/CTkToolTip/
- Existing codebase patterns: job_radar/gui/search_controls.py, job_radar/gui/profile_form.py, job_radar/profile_manager.py

### Secondary (MEDIUM confidence)
- CTkCollapsiblePanel GitHub: https://github.com/maxverwiebe/CTkCollapsiblePanel
- Tkinter collapsible pane patterns: https://www.tutorialspoint.com/collapsible-pane-in-tkinter-python
- Python GUI best practices (Tkinter): https://medium.com/tomtalkspython/tkinter-best-practices-optimizing-performance-and-code-structure-c49d1919fbb4

### Tertiary (LOW confidence)
- None — all key findings verified with official documentation or existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - CustomTkinter, CTkToolTip are official/well-documented; existing codebase confirms usage patterns
- Architecture: HIGH - Patterns verified with official docs + existing codebase (SearchControls, ProfileForm demonstrate validation, callbacks, grid layout)
- Pitfalls: MEDIUM-HIGH - Derived from CustomTkinter documentation (number_of_steps), user decisions (minimum weight 0.05), and general GUI best practices (validation timing)

**Research date:** 2026-02-13
**Valid until:** 2026-03-13 (30 days; CustomTkinter is stable, patterns unlikely to change)
