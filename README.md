# 🤖 WALL-E and EVE's Signal

### An autonomous search agent powered by Python

**WALL-E and EVE's Signal** is a beginner-friendly AI project that simulates WALL-E searching for EVE in an unknown grid environment. Using sensor observations, probability-based belief updates, and energy-aware planning, WALL-E makes autonomous decisions to navigate the environment, investigate signals, recharge when necessary, and locate EVE.

The project combines fundamental artificial intelligence concepts with a real-time visual dashboard to demonstrate how an autonomous agent can perceive its environment, reason from incomplete information, and adapt its actions to achieve a goal.

## ✨ Key Features

- 🧠 **Belief-Based Reasoning** — Maintains and updates probability estimates of EVE's possible location using sensor evidence.
- 🧭 **Autonomous Navigation** — Uses directional clues to guide movement instead of relying entirely on fixed exploration patterns.
- 🔋 **Energy-Aware Planning** — Monitors battery levels and plans safe returns to the charging station.
- 🌍 **Simulated Grid Environment** — Models movement, scanning, charging, sensor observations, and mission completion.
- 📊 **Live Tkinter Dashboard** — Visualizes the grid, battery level, visited cells, current operating mode, and decision log.
- 📝 **Mission Logging** — Records actions, observations, decisions, and explanations in a JSON execution trace.
- 📄 **Automatic Mission Report** — Summarizes the mission outcome, collected evidence, estimated location, confidence, and recommended next steps.
- 🧪 **Headless Execution** — Supports running the simulation without opening the GUI.

## 🛠️ Technologies Used

- Python
- Tkinter
- JSON
- Probability-based belief updates
- Autonomous agents and rule-based planning

## 🚀 Getting Started

Clone the repository, open the project folder in VS Code, and run:

```bash
python main.py
```

To run the simulation without the graphical interface:

```bash
python main.py --headless
```

## 📂 Project Outputs

The simulation generates:

- `outputs/action_trace.json` — The sequence of actions, observations, and decisions.
- `outputs/mission_report.json` — The final mission status and summary.

## 🎯 Learning Objectives

This project explores autonomous agents, observation-driven decision-making, uncertainty, sensor interpretation, resource management, and simulation-based testing.

It is designed as an educational demonstration of core AI concepts in a small, interactive environment.

---

*Built as a college AI/ML project to explore how autonomous agents can reason, navigate, and make decisions under uncertainty.*