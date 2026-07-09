# Detective-Board Collaborative Canvas 

A lightweight, real-time Kanban and brainstorming board built entirely in a single file. Designed with a strict local-development paradigm, this project eliminates complex build steps, node dependencies, and database setups in favor of raw Python and Vanilla JavaScript.

##  Features

* **Infinite Free-Form Canvas:** Drag and drop interactive sticky notes anywhere on the board.
* **Detective Strings:** Visually connect related cards with dynamic, auto-updating SVG lines.
* **Flyweight Stamp Library:** Quickly mark cards with status indicators (✅, ❌, ⚠️, 🔍) using a centralized, low-memory asset library.
* **Real-Time Collaboration:** Multi-user synchronization using a split-state heartbeat lock. If a user is actively editing or dragging a card, it is instantly locked for everyone else to prevent data collisions.
* **Pass-Through Authentication:** Frictionless entry. No passwords or registration—just enter a detective name and join the board.

##  Architecture & Tech Stack

To maximize context retention and ensure absolute simplicity, the entire application (Backend + Frontend) is housed within `main.py`.

* **Backend:** Python 3.11+, FastAPI, Uvicorn
* **Frontend:** HTML5 Canvas/SVG, Vanilla JavaScript, Tailwind CSS (via CDN)
* **Concurrency:** Native Python `asyncio.Queue` background worker processing a FIFO pipeline.
* **Persistent State:** A single `state.json` file handled exclusively by the background worker to eliminate file I/O locks.
* **Volatile State:** Ephemeral RAM-only dictionaries handling user session locks and heartbeat pings.

##  Local Quick Start

**1. Clone the repository:**
```bash
git clone https://github.com/BeetlesTheHunter/KanBanBoard
```

**2. Create and activate a Virtual Environment:**

*Linux / Mac:*
```bash
python3 -m venv venv
source venv/bin/activate
```

*Windows:*
```cmd
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies:**
This project requires FastAPI and Uvicorn. Ensure your virtual environment is activated, then install them via the terminal:
```bash
pip install -r requirements.txt
```

**4. Launch the Server:**
```bash
uvicorn main:app --reload --port 8000
```

**5. Open the Board:**
Navigate to `http://localhost:8000` in your web browser. 
*(Pro-tip: Open a second Incognito/Private window to the same address to easily simulate multi-user collaboration and test the locking mechanisms!)*

##  Project Structure

```text
.
├── main.py             # The complete application (FastAPI routing + HTML/JS UI)
├── requirements.txt    # Python package dependencies
├── state.json          # Auto-generated database file (Ignored in Git)
├── README.md           # Project documentation
└── .gitignore          # Git exclusion rules
```
