
import re

def check_balance(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Simple check for braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    print(f"{{: {open_braces}, }}: {close_braces}")

    open_parens = content.count('(')
    close_parens = content.count(')')
    print(f"(: {open_parens}, ): {close_parens}")

    # Check for tags (simplified)
    # This is not a full parser, just a heuristic
    tags = re.findall(r'</?(\w+)', content)
    stack = []
    
    # Void elements in HTML
    void_elements = {'img', 'br', 'hr', 'input', 'meta', 'link'}
    
    # We are parsing JSX, so components might be self-closing
    # But regex above doesn't catch self-closing />
    
    # Let's count specific tags
    for tag in ['div', 'span', 'p', 'header', 'h1', 'h3', 'Link']:
        opens = len(re.findall(rf'<{tag}\b', content))
        closes = len(re.findall(rf'</{tag}>', content))
        print(f"<{tag}>: {opens}, </{tag}>: {closes}")

check_balance('frontend/app/admin/dashboard/page.tsx')
