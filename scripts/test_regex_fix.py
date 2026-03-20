
import re

def test_regex():
    patterns = [
        (r'\[result\s+from\s+step\s+\d+\]', "REPLACED", re.IGNORECASE),
        (r'\[step\s+\d+\s+result\]', "REPLACED", re.IGNORECASE),
    ]

    queries = [
        "What is [step 1 result]?",
        "What is [step  1 result]?",
        "What is [Result From Step 1]?",
        "What is [result from step 1]?",
    ]

    for q in queries:
        original = q
        for pattern, repl, flags in patterns:
            if re.search(pattern, q, flags):
                q = re.sub(pattern, repl, q, flags=flags)
        print(f"Original: {original} -> Replaced: {q}")

if __name__ == "__main__":
    test_regex()
