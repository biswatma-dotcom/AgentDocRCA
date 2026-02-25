import os
import json
from openai import OpenAI


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def normalize_requirements(raw_text: str) -> list:
    """
    Use OpenAI to convert raw requirement text into a JSON array of 
    short, unambiguous, testable bullet points.
    """
    prompt = """Convert the following client requirement into a strict JSON array of short, unambiguous, testable bullet points. 
Return ONLY valid JSON (a JSON array of strings). Each bullet should be:
- Concise (under 50 characters)
- Unambiguous
- Testable/verifiable

Input requirements:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a requirements analyst. Convert raw requirements into normalized, testable bullet points. Return ONLY valid JSON array."},
                {"role": "user", "content": prompt + raw_text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        bullets = json.loads(content.strip())
        
        if isinstance(bullets, list):
            return bullets
        return []
        
    except Exception as e:
        print(f"Error normalizing requirements: {e}")
        return []
