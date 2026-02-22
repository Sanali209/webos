import pathlib
import sys

def verify_markdown_python_blocks():
    docs_dir = pathlib.Path("docs")
    if not docs_dir.exists():
        print("docs directory not found")
        return
        
    error_count = 0
    for md_file in docs_dir.rglob("*.md"):
        content = md_file.read_text()
        blocks = []
        is_in_block = False
        current_block = []
        
        for line in content.splitlines():
            if line.startswith("```python"):
                is_in_block = True
                current_block = []
            elif line.startswith("```") and is_in_block:
                is_in_block = False
                blocks.append("\n".join(current_block))
            elif is_in_block:
                current_block.append(line)
                
        for i, code in enumerate(blocks):
            try:
                compile(code, f"{md_file.name}_block_{i}", 'exec')
            except SyntaxError as e:
                print(f"Syntax Validation Failed in {md_file.name}, Block {i}:")
                print(e)
                error_count += 1
                
    if error_count == 0:
        print("✅ All Python examples in documentation are syntactically valid!")
    else:
        print(f"❌ Found {error_count} syntax errors in documentation.")
        sys.exit(1)

if __name__ == "__main__":
    verify_markdown_python_blocks()
