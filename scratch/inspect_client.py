import os

path = r"c:\dev\quant\.venv\Lib\site-packages\google\generativeai\client.py"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        if "v1beta" in line:
            print(f"Line {idx+1}: {line.strip()}")
            # Print preceding and succeeding 3 lines
            start = max(0, idx - 3)
            end = min(len(lines), idx + 4)
            for i in range(start, end):
                print(f"  {i+1}: {lines[i].rstrip()}")
            print("-" * 40)
else:
    print("client.py not found")
