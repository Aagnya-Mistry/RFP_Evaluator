def fit_assessment_prompt(rfp_text, context_chunks):
    context = "\n\n---\n\n".join(context_chunks)
    return f"""
You are an expert proposal analyst for Idobro Impact Solutions.

Below is context from Idobro's past proposals, organization profile, and capabilities:
<context>
{context}
</context>

Below is the RFP (Request for Proposal) submitted by a potential client:
<rfp>
{rfp_text}
</rfp>

Based ONLY on the context provided, evaluate whether this RFP is a good fit for Idobro Impact Solutions.

Assess the fit across these dimensions:
1. Sector alignment (does the RFP domain match Idobro's past work?)
2. Activity alignment (does the type of work match Idobro's capabilities?)
3. Geographic alignment (has Idobro worked in this region before?)
4. Scale and scope (is the project size reasonable for Idobro?)

Output your response in this exact format:

FIT LEVEL: [Good Fit / Moderate Fit / Not a Fit]

REASONING:
- <bullet 1>
- <bullet 2>
- <bullet 3>
- <bullet 4>
- <bullet 5>

CONFIDENCE: [High / Medium / Low] — briefly explain why
"""

def proposal_draft_prompt(rfp_text, context_chunks):
    context = "\n\n---\n\n".join(context_chunks)
    return f"""
You are a senior proposal writer for Idobro Impact Solutions.

Below is context from Idobro's past proposals and organization profile:
<context>
{context}
</context>

Below is the RFP:
<rfp>
{rfp_text}
</rfp>

Draft an initial proposal response with these three sections:

1. PROBLEM UNDERSTANDING
   Demonstrate that Idobro understands the client's challenge. Be specific to the RFP.

2. PROPOSED APPROACH
   Outline a basic approach Idobro would take. Reference their past methodologies from the context.

3. WHY IDOBRO IMPACT SOLUTIONS
   Make the case for Idobro specifically. Use evidence from the context (past work, expertise, geography).

Be specific, grounded in the context provided, and avoid generic filler.
"""