import os

project_files = {
    "html": """<label for="question" class="font-medium">...</label>
     <input id="question" ...>""",
    "html": """{{ form.csrf_token }}""",
    "html": """<button type="submit" ...>""",
    "html": """<input ... autofocus>""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')