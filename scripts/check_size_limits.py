import os
import ast

MAX_FILE_LINES = 1000
MAX_FUNC_TOKENS = 4000 # Approx lines

def check_file_size(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        if len(lines) > MAX_FILE_LINES:
            print(f"WARNING: {filepath} has {len(lines)} lines (Limit: {MAX_FILE_LINES})")

def check_func_size(filepath):
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = node.end_lineno - node.lineno
                if length > 200: # Soft limit for function lines
                     print(f"WARNING: Function '{node.name}' in {filepath} is {length} lines long.")

def main():
    for root, _, files in os.walk("."):
        if "venv" in root or "node_modules" in root or ".git" in root: continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                check_file_size(path)
                check_func_size(path)

if __name__ == "__main__":
    main()
