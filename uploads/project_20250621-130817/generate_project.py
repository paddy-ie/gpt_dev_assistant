import os

project_files = {
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')