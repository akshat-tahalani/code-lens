<div align="center">

# 🚀 CodeLens

### *AI-Powered Code Analysis & Developer Assistant*

### 🧠 *Making Code Easier to Understand, Debug & Improve.*

</div>

---

# 📖 Overview

CodeLens is an AI-powered code analysis platform that helps developers understand, debug, optimize, and improve source code through intelligent analysis.

Instead of simply executing code, CodeLens explains **why** the code behaves the way it does.

Whether you're a beginner learning programming or an experienced developer reviewing complex projects, CodeLens acts like an AI teammate.

---

# ✨ Features

## 🔍 Intelligent Code Analysis

- Detect bugs
- Identify logical errors
- Explain code execution
- Complexity analysis
- Code quality evaluation

---

## 🤖 AI Explanations

Generate beginner-friendly explanations for:

- Functions
- Classes
- Loops
- Recursion
- Data Structures
- Algorithms

---

## ⚡ Performance Suggestions

Receive recommendations for

- Cleaner code
- Faster algorithms
- Better practices
- Memory optimization

---

## 📊 Complexity Analysis

Automatically estimate

- Time Complexity
- Space Complexity
- Performance Bottlenecks

---

## 🎯 Beginner Friendly

CodeLens doesn't just tell you what's wrong.

It teaches:

- Why it's wrong
- How to fix it
- Better alternatives
- Best practices

---

# 🎥 Demo

> *(Replace with your project GIF later)*

<p align="center">

<img src="images/demo.gif" width="900">

</p>

---

# 🏗️ Architecture

```text
                User
                  │
                  ▼
          React Frontend
                  │
                  ▼
        REST API (FastAPI)
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
 AI Analysis Engine      Database
      │
      ▼
 Generated Insights
      │
      ▼
 JSON Response
      │
      ▼
Frontend Visualization
```

---

# 🛠️ Tech Stack

| Technology | Purpose |
|------------|----------|
| Python | Backend |
| FastAPI | REST API |
| React | Frontend |
| JavaScript | UI Logic |
| AI Models | Code Understanding |
| Git | Version Control |
| GitHub | Repository Hosting |

---

# 📂 Project Structure

```text
CodeLens/

│
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── routes/
│   ├── utils/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── assets/
│   └── public/
│
├── docs/
│
├── images/
│
├── README.md
│
└── requirements.txt
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/USERNAME/CodeLens.git
```

```bash
cd CodeLens
```

---

## Backend

```bash
pip install -r requirements.txt
```

Run FastAPI

```bash
uvicorn main:app --reload
```

---

## Frontend

```bash
npm install
```

```bash
npm run dev
```

---

# 🚀 API Example

### Request

```http
POST /analyze
```

```json
{
  "code":"print('Hello World')"
}
```

### Response

```json
{
  "complexity":"O(1)",
  "bugs":0,
  "suggestions":[
      "Code looks clean."
  ]
}
```

---

# 🌟 Future Roadmap

- [ ] AI Bug Detection
- [ ] Multi-language Support
- [ ] AST Visualization
- [ ] Execution Flow Animation
- [ ] Complexity Prediction
- [ ] GitHub Integration
- [ ] VS Code Extension
- [ ] AI Chat Assistant
- [ ] Code Refactoring Suggestions
- [ ] Interactive Learning Mode

---

# 🤝 Contributing

Contributions are always welcome!

If you'd like to improve CodeLens:

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

# 📈 Project Goals

✔ Help beginners understand programming

✔ Simplify debugging

✔ Improve coding skills

✔ Make AI-assisted learning accessible

✔ Build an intelligent developer companion

---

# 📸 Screenshots

| Dashboard | Analysis |
|-----------|----------|
| ![](images/dashboard.png) | ![](images/analysis.png) |

---

# 💡 Inspiration

Modern developers spend a significant amount of time understanding existing code rather than writing new code.

CodeLens aims to bridge that gap by combining AI with intuitive explanations to make programming more approachable, educational, and productive.

---

<div align="center">

## ⭐ If you like this project, consider giving it a star!

### Made with ❤️ using FastAPI, React & AI

</div>
