import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def judge_sql_query(generated_query: str, ground_truth_query: str, prompt: str = "") -> dict:
    system_prompt = """You are an expert SQL query evaluator. Your task is to compare a generated SQL query against a ground truth query and provide a detailed assessment.

You should evaluate on multiple dimensions:
1. **Semantic Equivalence**: Do both queries accomplish the same goal?
2. **Syntactic Similarity**: How similar is the structure and syntax?
3. **Correctness**: Would the generated query produce the correct results?
4. **Efficiency**: Is the generated query reasonably efficient?

Provide your response in the following format:
SCORE: [A decimal number between 0.0 and 1.0]
SEMANTIC_MATCH: [YES or NO - are they functionally equivalent?]
REASONING: [Detailed explanation of your evaluation]

Scoring guidelines:
- 1.0: Queries are functionally identical or semantically equivalent
- 0.8-0.9: Minor differences (e.g., column order, aliases) but produces same results
- 0.6-0.7: Mostly correct but may have minor logic issues
- 0.4-0.5: Partially correct, captures some intent but has significant issues
- 0.2-0.3: Incorrect but shows some understanding
- 0.0-0.1: Completely wrong or invalid SQL"""

    user_prompt = f"""Evaluate this SQL query generation:

GROUND TRUTH QUERY:
```sql
{ground_truth_query}
```

GENERATED QUERY:
```sql
{generated_query}
```
"""

    if prompt:
        user_prompt += f"""
ORIGINAL REQUEST:
{prompt}
"""

    user_prompt += """
Please provide your evaluation following the specified format."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent evaluation
        )
        
        evaluation_text = response.choices[0].message.content
        
        # Parse the response
        score = 0.0
        semantic_match = False
        reasoning = evaluation_text
        
        lines = evaluation_text.split('\n')
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score_str = line.replace('SCORE:', '').strip()
                    score = float(score_str)
                    # Clamp score between 0 and 1
                    score = max(0.0, min(1.0, score))
                except ValueError:
                    pass
            elif line.startswith('SEMANTIC_MATCH:'):
                match_str = line.replace('SEMANTIC_MATCH:', '').strip().upper()
                semantic_match = match_str == 'YES'
            elif line.startswith('REASONING:'):
                # Get all text after REASONING:
                reasoning_start = evaluation_text.find('REASONING:')
                if reasoning_start != -1:
                    reasoning = evaluation_text[reasoning_start + len('REASONING:'):].strip()
        
        return {
            "score": score,
            "semantic_match": semantic_match,
            "reasoning": reasoning,
            "raw_evaluation": evaluation_text
        }
        
    except Exception as e:
        return {
            "score": 0.0,
            "semantic_match": False,
            "reasoning": f"Error during evaluation: {str(e)}",
            "raw_evaluation": "",
            "error": str(e)
        }
