
import re
import unittest

class TestPlaceholderExtraction(unittest.TestCase):
    def test_extraction(self):
        sub_query = "What year was [step 1 result] born?"
        explicit_step_patterns = [
            r'\[Result\s+from\s+Step\s+(\d+)\]',  # [Result from Step 3]
            r'\[result\s+from\s+step\s+(\d+)\]',  # [result from step 3]
            r'\[step\s+(\d+)\s+result\]',  # [step 3 result]
            r'\[步骤(\d+)的结果\]',  # [步骤3的结果]
        ]
        
        explicit_step_num = None
        for pattern in explicit_step_patterns:
            match = re.search(pattern, sub_query, re.IGNORECASE)
            if match:
                step_num_from_placeholder = int(match.group(1))
                explicit_step_num = step_num_from_placeholder - 1
                break
        
        print(f"Query: {sub_query}")
        print(f"Extracted step num: {explicit_step_num}")
        self.assertEqual(explicit_step_num, 0)

    def test_extraction_double_space(self):
        sub_query = "What year was [step  1 result] born?"
        explicit_step_patterns = [
            r'\[Result\s+from\s+Step\s+(\d+)\]',  # [Result from Step 3]
            r'\[result\s+from\s+step\s+(\d+)\]',  # [result from step 3]
            r'\[step\s+(\d+)\s+result\]',  # [step 3 result]
            r'\[步骤(\d+)的结果\]',  # [步骤3的结果]
        ]
        
        explicit_step_num = None
        for pattern in explicit_step_patterns:
            match = re.search(pattern, sub_query, re.IGNORECASE)
            if match:
                step_num_from_placeholder = int(match.group(1))
                explicit_step_num = step_num_from_placeholder - 1
                break
        
        print(f"Query: {sub_query}")
        print(f"Extracted step num: {explicit_step_num}")
        self.assertEqual(explicit_step_num, 0)

if __name__ == '__main__':
    unittest.main()
