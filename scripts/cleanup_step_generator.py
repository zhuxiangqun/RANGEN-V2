import os

file_path = 'src/core/reasoning/step_generator.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'def _get_fallback_reasoning_steps_prompt' in line:
        start_line = i
    if 'def _retry_llm_with_specific_name_feedback' in line:
        end_line = i
        break

if start_line != -1 and end_line != -1:
    # Find the return statement start
    return_start = -1
    for i in range(start_line, end_line):
        if 'return f"""**🚨🚨🚨 CRITICAL TASK DEFINITION' in lines[i]:
            return_start = i
            break
            
    if return_start != -1:
        new_lines = lines[:return_start]
        new_lines.append('        # Fallback to a simple message if prompt generator fails and templates are missing\n')
        new_lines.append('        return "Detailed reasoning prompt not available. Please ensure templates.json is loaded correctly."\n\n')
        new_lines.append('    ' + lines[end_line].strip() + '\n') # Re-add the next function def line properly indented? No, function def is usually indented 4 spaces inside class
        
        # Wait, lines[end_line] is the next function definition.
        # We should append lines[end_line:]
        
        final_lines = lines[:return_start]
        final_lines.append('        # Fallback to a simple message if prompt generator fails and templates are missing\n')
        final_lines.append('        return "Detailed reasoning prompt not available. Please ensure templates.json is loaded correctly."\n\n')
        final_lines.extend(lines[end_line:])
        
        with open(file_path, 'w') as f:
            f.writelines(final_lines)
        print("Successfully cleaned up _get_fallback_reasoning_steps_prompt")
    else:
        print("Could not find the return statement start")
else:
    print(f"Could not find function boundaries: start={start_line}, end={end_line}")

