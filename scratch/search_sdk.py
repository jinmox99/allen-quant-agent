import os

path = r"c:\dev\quant\.venv\Lib\site-packages\google\generativeai"
if os.path.exists(path):
    print("Package directory exists!")
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "v1beta" in content:
                            print(f"- Found v1beta in {os.path.relpath(filepath, path)}")
                except Exception as e:
                    pass
else:
    print("Package directory not found at", path)
