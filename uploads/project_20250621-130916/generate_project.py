import os

project_files = {
    "output.txt": """ai-local-business-accelerator/
│
├── backend/                # Django or FastAPI project
│   ├── manage.py
│   ├── accelerator/        # Django project settings
│   └── apps/
│       ├── users/          # Auth, business/shoppers
│       ├── businesses/     # Business profiles, onboarding, inventory
│       ├── campaigns/      # Marketing automation
│       ├── marketplace/    # Shopfronts, products, checkout
│       └── analytics/      # Reports, insights
│
├── frontend/               # React.js app
│   ├── admin-dashboard/    # For business owners
│   └── shopper-app/        # For shoppers (web/mobile)
│
├── mobile/                 # React Native app (optional)
│
├── docs/                   # Architecture, onboarding, API docs
│
└── devops/                 # Docker, CI/CD, infra scripts""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')