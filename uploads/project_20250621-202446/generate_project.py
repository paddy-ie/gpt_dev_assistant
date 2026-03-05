import os

project_files = {
    "html": """<label for="question" class="font-medium">💡 What do you want to do?</label>
     <input id="question" ...>""",
    "html": """<button type="submit" ...>""",
    "html": """{{ form.csrf_token }}""",
    "html": """<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">""",
    "html": """<input ... autofocus>""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')