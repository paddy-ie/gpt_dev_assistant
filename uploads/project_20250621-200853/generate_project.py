import os

project_files = {
    "output.txt": """ai-local-business-accelerator/
│
├── backend/                # Python FastAPI or Django backend
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── ai/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── frontend/               # React web dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   ├── public/
│   └── package.json
│
├── mobile/                 # React Native app for iOS/Android
│   ├── src/
│   │   ├── components/
│   │   └── App.js
│   └── package.json
│
├── devops/                 # CI/CD, Docker, infra as code
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── github-actions.yml
│
└── README.md""",
    "python": """from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "AI Local Business Accelerator API"}""",
    "jsx": """import React from 'react';

function App() {
  return (
    <div>
      <h1>AI Local Business Accelerator Dashboard</h1>
      <p>Welcome! Manage your business here.</p>
    </div>
  );
}

export default App;""",
    "javascript": """import React from 'react';
import { View, Text } from 'react-native';

export default function App() {
  return (
    <View>
      <Text>Shop Local Marketplace</Text>
    </View>
  );
}""",
    "markdown": """# AI Local Business Accelerator

A plug-and-play digital platform empowering local retailers and service providers in Ireland and the UK with AI-powered marketing, inventory, loyalty, and e-commerce tools.

## Monorepo Structure

- `backend/` — FastAPI/Django backend
- `frontend/` — React web dashboard
- `mobile/` — React Native shopper app
- `devops/` — Docker, CI/CD, infra

## Quick Start

1. `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
2. `cd frontend && npm install && npm start`
3. `cd mobile && npm install && npx expo start`""",
}

for path, content in project_files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('✅ Project files created successfully.')