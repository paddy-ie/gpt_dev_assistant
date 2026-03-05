import os

project_files = {
    "bash": """# Install Django if you haven't already
pip install django

# Start a new project
django-admin startproject tradesmean

# Move into the project directory
cd tradesmean

# Start an app (e.g., 'core')
python manage.py startapp core""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')