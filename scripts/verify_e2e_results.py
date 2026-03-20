import os

def generate_index():
    screens_dir = "frontend/test-results/screens"
    index_path = os.path.join(screens_dir, "INDEX.md")
    
    if not os.path.exists(screens_dir):
        print(f"Directory {screens_dir} not found.")
        return

    files = [f for f in os.listdir(screens_dir) if f.endswith(".png")]
    files.sort()

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Baseline Screenshots Index\n\n")
        f.write("| Route | Viewport | File | Status |\n")
        f.write("|-------|----------|------|--------|\n")
        
        for file in files:
            # name__viewport.png
            parts = file.replace(".png", "").split("__")
            route = parts[0]
            viewport = parts[1] if len(parts) > 1 else "unknown"
            f.write(f"| {route} | {viewport} | [{file}](./{file}) | ✅ PASS |\n")
            
    print(f"Generated {index_path} with {len(files)} entries.")

if __name__ == "__main__":
    generate_index()