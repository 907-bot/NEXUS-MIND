import os
import glob
import re

agents_dir = 'f:/nexus-mind/NexusMind/backend/app/agents/'
files = glob.glob(os.path.join(agents_dir, '*_agent.py'))
for f in files:
    if 'base_agent.py' in f or 'planner_agent.py' in f or 'assembler_agent.py' in f: continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'next_agent' not in content:
        # Add next_agent to JSON prompt block
        content = content.replace('"summary":', '"next_agent": "AgentName",\n  "summary":')
        
        # Add next_agent to the output dict returned by execute
        content = content.replace('"summary": result.get("summary", ""),', '"next_agent": result.get("next_agent", "AssemblerAgent"),\n            "summary": result.get("summary", ""),')

        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {os.path.basename(f)}")
