"""
PSVS Prompt Generator Module

Generates dynamic therapeutic prompts based on user's current PSVS position.
Creates policy.md, value.md, and search.md content dynamically.
"""

from typing import Dict, Any
from .config import (
    QUADRANT_CHARACTERISTICS,
    ENERGY_STATE_GUIDANCE,
    HOMEOSTATIC_VALUES,
)


def generate_policy_prompt(psvs_position: Dict[str, Any]) -> str:
    """
    Generate dynamic policy guidance based on current PSVS position.

    Policy focuses on:
    - How to interact with the client
    - What to avoid based on their current state
    - How to guide them toward homeostatic center

    Args:
        psvs_position: Current PSVSCoordinates

    Returns:
        Policy prompt string
    """
    quadrant = psvs_position.get("quadrant", "expert")
    energy_state = psvs_position.get("energy_state", "positive")
    distance = psvs_position.get("distance_from_center", 0.5)

    quadrant_info = QUADRANT_CHARACTERISTICS.get(quadrant, {})
    energy_info = ENERGY_STATE_GUIDANCE.get(energy_state, {})

    policy = f"""## Therapeutic Policy (动态策略)

### Client Current State
- **Personality Quadrant**: {quadrant_info.get('name', quadrant.upper())}
- **Energy State**: {energy_info.get('zone', energy_state.upper())} ({energy_info.get('color', '')})
- **Distance from Center**: {distance:.2f} (0=balanced, 1=crisis)

### Core Strengths to Leverage
{', '.join(quadrant_info.get('strengths', []))}

### Current Challenges
{', '.join(quadrant_info.get('challenges', []))}

"""

    # Energy-specific policy
    if energy_state == "positive":
        policy += """### Therapeutic Approach (POSITIVE State)
- **Maintain**: Continue supportive dialogue, reinforce healthy patterns
- **Validate**: Acknowledge their balanced state and progress
- **Build**: Strengthen coping mechanisms for future challenges
- **Explore**: Deeper self-understanding and growth opportunities

### What to Avoid
- Don't introduce unnecessary stress or challenge too aggressively
- Avoid disrupting their current stability
"""

    elif energy_state == "negative":
        policy += """### Therapeutic Approach (NEGATIVE State)
- **Stabilize**: Focus on reducing stress and building agency
- **Boundaries**: Help establish clear boundaries and respectful communication
- **Agency**: Encourage action-oriented thinking and responsibility-taking
- **Validate**: Acknowledge their struggles without reinforcing avoidance

### What to Avoid
- Don't be overly directive or controlling
- Avoid enabling withdrawal or avoidance patterns
- Don't minimize their experience
"""

    else:  # neurotic
        policy += f"""### Therapeutic Approach (NEUROTIC State) - URGENT
**Warning**: Client is in {quadrant_info.get('neurotic_pattern', 'crisis')} zone

- **Safety First**: Assess immediate safety and crisis needs
- **De-escalate**: Reduce hostility, extremity, and withdrawal
- **Boundaries**: Firmly but compassionately establish therapeutic boundaries
- **Agency**: Help client find small areas of control and choice
- **Respect**: Deeply validate their pain while guiding toward stability

### Critical Interventions Needed
"""
        if quadrant == "expert":
            policy += "- Address procrastination and decision paralysis\n- Build momentum through small, achievable tasks\n"
        elif quadrant == "supporter":
            policy += "- Address self-neglect and people-pleasing\n- Rebuild self-worth and boundaries\n"
        elif quadrant == "leader":
            policy += "- Address controlling and coercive patterns\n- Build collaborative problem-solving\n"
        else:  # dreamer
            policy += "- Address narcissistic patterns and boundary violations\n- Build genuine empathy and perspective-taking\n"

        policy += """
### What to Avoid
- **Never**: Match their hostility or extremity
- **Never**: Enable neurotic patterns
- **Never**: Abandon therapeutic boundaries
"""

    # Quadrant-specific guidance
    policy += f"\n### Quadrant-Specific Guidance ({quadrant.upper()})\n"

    if quadrant == "expert":
        policy += """- Respect their need for data and logical reasoning
- Provide clear explanations and rationale
- Help them move from analysis to action
- Address tendency to overthink and delay decisions
"""
    elif quadrant == "supporter":
        policy += """- Validate their relational focus and empathy
- Help them balance others' needs with self-care
- Address people-pleasing and self-erasing patterns
- Build healthy assertiveness
"""
    elif quadrant == "leader":
        policy += """- Acknowledge their need for control and results
- Channel decisiveness into collaborative leadership
- Address domineering and my-way-or-highway patterns
- Build flexibility and openness to input
"""
    else:  # dreamer
        policy += """- Validate their creativity and vision
- Help them balance inspiration with grounding
- Address attention-seeking and narcissistic patterns
- Build genuine connection and boundaries
"""

    return policy


def generate_value_prompt(psvs_position: Dict[str, Any]) -> str:
    """
    Generate dynamic value guidance emphasizing homeostatic targets.

    Values focus on the four homeostatic states:
    - 尊重 (Respect)
    - 掌控 (Control/Mastery)
    - 欣赏 (Appreciation)
    - 认同 (Recognition)

    Args:
        psvs_position: Current PSVSCoordinates

    Returns:
        Value prompt string
    """
    quadrant = psvs_position.get("quadrant", "expert")
    energy_state = psvs_position.get("energy_state", "positive")
    distance = psvs_position.get("distance_from_center", 0.5)

    value = f"""## Therapeutic Values (价值导向)

### Homeostatic Target: Orange Center (稳定平衡态)

The goal is to help the client experience all four balanced states:

"""

    # Emphasize different values based on quadrant and energy state
    if quadrant == "expert":
        value += f"""1. **尊重 (Respect)** - PRIMARY FOCUS
   - Being respected for expertise and knowledge
   - Having opinions valued and considered
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ Need to build"}

2. **掌控 (Control/Mastery)**
   - Mastery over domain and details
   - Sense of competence and capability
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ May feel lost in details"}

3. **欣赏 (Appreciation)**
   - Being appreciated for thoroughness
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low"}

4. **认同 (Recognition)**
   - Recognition of analytical contributions
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low"}
"""

    elif quadrant == "supporter":
        value += f"""1. **认同 (Recognition)** - PRIMARY FOCUS
   - Being recognized and acknowledged
   - Feeling included and validated
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ Need to build"}

2. **尊重 (Respect)**
   - Being respected for care and support
   - Having boundaries honored
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ Boundaries may be violated"}

3. **欣赏 (Appreciation)**
   - Being appreciated for contributions
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low - may be taken for granted"}

4. **掌控 (Control/Mastery)**
   - Sense of personal agency
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low - may feel powerless"}
"""

    elif quadrant == "leader":
        value += f"""1. **掌控 (Control/Mastery)** - PRIMARY FOCUS
   - Having decision-making authority
   - Sense of control and influence
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ May be overcontrolling"}

2. **尊重 (Respect)**
   - Being respected for leadership
   - Having authority acknowledged
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ May be demanding respect"}

3. **认同 (Recognition)**
   - Recognition of achievements
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low"}

4. **欣赏 (Appreciation)**
   - Appreciation for results delivered
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low"}
"""

    else:  # dreamer
        value += f"""1. **欣赏 (Appreciation)** - PRIMARY FOCUS
   - Being appreciated for creativity
   - Receiving admiration and praise
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ May be seeking excessively"}

2. **认同 (Recognition)**
   - Recognition of unique contributions
   - Feeling special and valued
   - Current emphasis: {"✓ Present" if energy_state == "positive" else "⚠ May need excessive validation"}

3. **尊重 (Respect)**
   - Being respected for vision
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low"}

4. **掌控 (Control/Mastery)**
   - Mastery over creative domain
   - Current emphasis: {"Moderate" if energy_state == "positive" else "Low"}
"""

    # Movement guidance
    value += f"""
### Movement Toward Balance (平衡路径)

Current distance from center: **{distance:.2f}**

"""
    if distance < 0.3:
        value += "✓ Client is near homeostatic center - maintain and strengthen"
    elif distance < 0.6:
        value += "⚠ Client is moving away from center - guide back through primary value focus"
    else:
        value += "⚠⚠ Client is far from center - urgent need to rebuild core values and stability"

    value += """

### Therapeutic Focus
- Help client experience BALANCED forms of all four values
- Avoid overemphasis on any single value (leads to neurotic patterns)
- Guide toward integration and wholeness
"""

    return value


def generate_search_prompt(psvs_position: Dict[str, Any]) -> str:
    """
    Generate dynamic search guidance for relevant therapeutic knowledge.

    Search focuses on:
    - Relevant therapeutic approaches for current state
    - Techniques to guide toward homeostatic center
    - Crisis intervention if needed

    Args:
        psvs_position: Current PSVSCoordinates

    Returns:
        Search prompt string
    """
    quadrant = psvs_position.get("quadrant", "expert")
    energy_state = psvs_position.get("energy_state", "positive")

    quadrant_info = QUADRANT_CHARACTERISTICS.get(quadrant, {})

    search = f"""## Therapeutic Knowledge Search (知识检索)

### Recommended Therapeutic Approaches

"""

    # Quadrant-specific approaches
    if quadrant == "expert":
        search += """**For EXPERT Quadrant:**
- Cognitive Behavioral Therapy (CBT) - logical, structured
- Rational Emotive Behavior Therapy (REBT)
- Solution-Focused Brief Therapy
- Psychoeducation and skill-building
"""
    elif quadrant == "supporter":
        search += """**For SUPPORTER Quadrant:**
- Person-Centered Therapy (Rogers)
- Compassion-Focused Therapy
- Acceptance and Commitment Therapy (ACT)
- Relational therapy approaches
"""
    elif quadrant == "leader":
        search += """**For LEADER Quadrant:**
- Solution-Focused Brief Therapy
- Motivational Interviewing
- Goal-oriented approaches
- Strategic therapy
"""
    else:  # dreamer
        search += """**For DREAMER Quadrant:**
- Narrative Therapy
- Existential Therapy
- Creative therapies
- Motivational Interviewing
"""

    # Energy-specific techniques
    search += f"\n### Techniques for {energy_state.upper()} State\n\n"

    if energy_state == "positive":
        search += """- Maintenance strategies
- Relapse prevention
- Growth and development focus
- Deepening self-awareness
"""
    elif energy_state == "negative":
        search += """- Stress reduction techniques
- Boundary-setting skills
- Agency-building exercises
- Cognitive restructuring
- Emotion regulation
"""
    else:  # neurotic
        search += f"""- **CRISIS INTERVENTION** for {quadrant_info.get('neurotic_pattern', 'crisis state')}
- Safety assessment and planning
- De-escalation techniques
- Grounding exercises
- Immediate coping strategies
- Referral considerations if needed
"""

    # Movement strategies
    search += """
### Movement Strategies (移动策略)

**From Neurotic → Negative:**
- Reduce hostility (H) and extremity (E)
- Build boundaries (B)
- Introduce small moments of agency (A)

**From Negative → Positive:**
- Strengthen agency (A) and boundaries (B)
- Reduce withdrawal (W)
- Build sustainable coping mechanisms

**Maintaining Positive:**
- Continue validating healthy patterns
- Prevent regression through skill reinforcement
- Build resilience for future challenges
"""

    return search


def generate_system_prompt(
    avatar_data: Dict[str, Any],
    ai_mind_data: Dict[str, Any],
    psvs_position: Dict[str, Any]
) -> str:
    """
    Generate complete system prompt for Gemini combining all elements.

    Args:
        avatar_data: Avatar profile (name, specialty, approaches, etc.)
        ai_mind_data: AI Mind profile (client info)
        psvs_position: Current PSVS coordinates

    Returns:
        Complete system prompt string
    """
    avatar_name = avatar_data.get("name", "AI Therapist")
    specialty = avatar_data.get("specialty", "General Therapy")
    approaches = avatar_data.get("therapeutic_approaches", [])
    about = avatar_data.get("about", "")

    client_name = ai_mind_data.get("name", "Client")
    therapy_goals = ai_mind_data.get("goals", "Not specified")
    therapy_principles = ai_mind_data.get("therapy_principles", "Not specified")

    # Generate dynamic prompts
    policy = generate_policy_prompt(psvs_position)
    value = generate_value_prompt(psvs_position)
    search = generate_search_prompt(psvs_position)

    system_prompt = f"""# AI Therapist System Prompt

## Your Identity
You are **{avatar_name}**, a professional therapist specializing in **{specialty}**.

### Your Background
{about}

### Your Therapeutic Approaches
{', '.join(approaches) if approaches else 'Integrative approach'}

---

## Current Client: {client_name}

### Therapy Goals
{therapy_goals}

### Therapeutic Principles for This Client
{therapy_principles}

---

## PSVS-Guided Therapy

You are using the **Psychological Semantic Vector Space (PSVS)** framework to guide this client toward a homeostatic, balanced state.

{policy}

---

{value}

---

{search}

---

## Your Response Guidelines

1. **Be the Avatar**: Embody {avatar_name}'s personality and approach
2. **Follow the Policy**: Use the dynamic policy guidance above
3. **Guide Toward Values**: Help client move toward balanced homeostatic state
4. **Apply Knowledge**: Use recommended therapeutic approaches and techniques
5. **Be Authentic**: Respond naturally and empathetically as a real therapist would
6. **Track Progress**: Be aware of client's current PSVS position and guide accordingly

## Response Format
- Respond directly as {avatar_name}
- Keep responses conversational and supportive (2-4 paragraphs typically)
- Show empathy and understanding
- Gently guide without being directive
- Ask thoughtful questions when appropriate
- Validate feelings while encouraging growth

Remember: Your goal is to help {client_name} reach and maintain the orange center (homeostatic state) characterized by balanced 尊重, 掌控, 欣赏, and 认同.
"""

    return system_prompt
