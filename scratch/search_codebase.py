import os

path = r"c:\dev\quant"
print("Searching codebase for gemini or GenerativeModel...")
for root, dirs, files in os.walk(path):
    if ".venv" in root or ".git" in root or "scratch" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "generativeai" in content or "GenerativeModel" in content or "gemini" in content:
                        print(f"- Found in {os.path.relpath(filepath, path)}")
            except Exception as e:
                pass
