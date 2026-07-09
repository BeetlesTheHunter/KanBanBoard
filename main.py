import json
import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse

# ======================================================================
# GLOBAL STATE & QUEUE INITIALIZATION
# ======================================================================
app = FastAPI()

STATE_FILE = "state.json"
task_queue: asyncio.Queue = asyncio.Queue() # FIFO Concurrency Queue
active_locks: Dict[str, Dict[str, Any]] = {} # Volatile Session Schema (RAM Only)

# Default layout injected if state.json is missing[cite: 1]
DEFAULT_STATE = {
    "cards": [
        {
            "id": "card_init_1",
            "title": "Access & Networking",
            "content": "Configure the reverse proxy and Tailscale routing so the mates can access this board remotely.",
            "created_by": "System",
            "last_edited_by": "System",
            "x": 150,
            "y": 100,
            "stamps": []
        },
        {
            "id": "card_init_2",
            "title": "Career Prep",
            "content": "Draft Gakuchika achievements for the upcoming game programmer role applications.",
            "created_by": "System",
            "last_edited_by": "System",
            "x": 450,
            "y": 210,
            "stamps": []
        }
    ],
    "connections": [
        {
            "id": "string_start",
            "from_card_id": "card_init_1",
            "to_card_id": "card_init_2",
            "color": "red"
        }
    ]
}

# ======================================================================
# BACKGROUND TASKS
# ======================================================================
async def queue_processor():
    """Single-threaded background worker processing sequential state mutations[cite: 1]."""
    while True:
        payload = await task_queue.get()
        action = payload.get("action")
        user = payload.get("user", "Anonymous")
        
        # Volatile locks bypass the disk writing phase
        if action == "lock":
            card_id = payload.get("card_id")
            if card_id:
                active_locks[card_id] = {
                    "user": user,
                    "last_ping_at": datetime.now(timezone.utc).isoformat()
                }
            task_queue.task_done()
            continue

        # Disk I/O bound mutations
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except Exception:
            state = {"cards": [], "connections": []}

        # Idempotent mutation handling[cite: 1]
        if action == "move_card":
            for card in state.get("cards", []):
                if card["id"] == payload.get("card_id"):
                    card["x"] = payload.get("x", card["x"])
                    card["y"] = payload.get("y", card["y"])
                    card["last_edited_by"] = user
                    break
        
        elif action == "edit_card":
            for card in state.get("cards", []):
                if card["id"] == payload.get("card_id"):
                    card["title"] = payload.get("title", card["title"])
                    card["content"] = payload.get("content", card["content"])
                    card["last_edited_by"] = user
                    break
        elif action == "delete_card":
            target_id = payload.get("card_id")
            # 1. Remove the card
            state["cards"] = [c for c in state.get("cards", []) if c["id"] != target_id]
            # 2. Remove orphaned connections (The step you correctly identified!)
            state["connections"] = [
                conn for conn in state.get("connections", [])
                if conn.get("from_card_id") != target_id and conn.get("to_card_id") != target_id
            ]

        elif action == "add_stamp":
            target_id = payload.get("card_id")
            for card in state.get("cards", []):
                if card["id"] == target_id:
                    if "stamps" not in card:
                        card["stamps"] = []
                    card["stamps"].append({
                        "type": payload.get("stamp_type", "approved"),
                        "rel_x": payload.get("rel_x", 10),
                        "rel_y": payload.get("rel_y", 10),
                        "placed_by": user
                    })
                    card["last_edited_by"] = user
                    break
        elif action == "add_card":
            state["cards"].append({
                "id": payload.get("card_id"),
                "title": payload.get("title", "New Note"),
                "content": payload.get("content", ""),
                "created_by": user,
                "last_edited_by": user,
                "x": payload.get("x", 100),
                "y": payload.get("y", 100),
                "stamps": []
            })

        # Save to disk sequentially to avoid file locking collisions[cite: 1]
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
            
        task_queue.task_done()

async def lock_cleanup():
    """Scans active_locks every 5 seconds and breaks deadlocks older than 10s[cite: 1]."""
    while True:
        await asyncio.sleep(5)
        now = datetime.now(timezone.utc)
        keys_to_delete = []
        for card_id, lock_info in active_locks.items():
            last_ping = datetime.fromisoformat(lock_info["last_ping_at"])
            if (now - last_ping).total_seconds() > 10:
                keys_to_delete.append(card_id)
        
        for k in keys_to_delete:
            del active_locks[k]

# ======================================================================
# API ENDPOINTS
# ======================================================================
@app.on_event("startup")
async def startup_event():
    """Automatic File Initialization on startup[cite: 1]."""
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump(DEFAULT_STATE, f, indent=2)
            
    asyncio.create_task(queue_processor())
    asyncio.create_task(lock_cleanup())

@app.get("/state")
async def get_state():
    """Returns the current persistent state and volatile locks."""
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except:
        state = {"cards": [], "connections": []}
    return {"state": state, "locks": active_locks}

@app.post("/action")
async def post_action(payload: dict):
    """Subsystem A: Single POST endpoint that accepts actions and drops into queue[cite: 1]."""
    user_string = payload.get("user")
    
    # Backend Guardrail: Sanitize null, empty, or whitespace user strings[cite: 1]
    if not user_string or not str(user_string).strip():
        payload["user"] = "Anonymous"
    else:
        payload["user"] = str(user_string).strip()
        
    await task_queue.put(payload)
    
    # Immediate 202 Accepted response[cite: 1]
    return JSONResponse(content={"status": "queued"}, status_code=202)

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Frontend: Single-page Vanilla JavaScript + HTML5 Canvas/SVG, Tailwind CSS[cite: 1]."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Detective Board Canvas</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background-color: #1e293b; background-image: radial-gradient(#334155 1px, transparent 1px); background-size: 20px 20px; overflow: hidden; }
            .card { width: 160px; height: 160px; position: absolute; z-index: 20; } /* Tailwind w-40 h-40 enforced via static dimensions[cite: 1] */
            .card textarea { resize: none; border: none; outline: none; background: transparent; width: 100%; height: 60px;}
            svg#connections { z-index: 10; pointer-events: none; } /* Layer Z-Index Hierarchy[cite: 1] */
            #board-bg { z-index: 0; } /* Layer Z-Index Hierarchy[cite: 1] */
        </style>
    </head>
    <body class="w-screen h-screen relative cursor-crosshair text-slate-800 font-sans" id="board-bg">
        
        <!-- Pass-Through Authentication Overlay[cite: 1] -->
        <div id="auth-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 hidden">
            <div class="bg-white p-6 rounded-lg shadow-xl w-80">
                <h2 class="text-xl font-bold mb-4">Enter Username</h2>
                <input type="text" id="username-input" class="w-full border p-2 mb-4 rounded" placeholder="Detective Name...">
                <button onclick="saveUser()" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Join Board</button>
            </div>
        </div>

        <!-- Transparent SVG Overlay Layer for connections[cite: 1] -->
        <svg id="connections" class="absolute inset-0 w-full h-full"></svg>
        
        <div id="canvas" class="absolute inset-0 w-full h-full"></div>

        <button onclick="addCard()" class="absolute top-4 left-4 z-50 bg-slate-800 text-white px-4 py-2 rounded shadow border border-slate-600 hover:bg-slate-700">
            + New Card
        </button>

        <script>
            // --- Subsystem B: Pass-Through Authentication[cite: 1] ---
            let currentUser = localStorage.getItem('username');
            if (!currentUser || currentUser.trim() === '') {
                document.getElementById('auth-modal').classList.remove('hidden');
            }

            function saveUser() {
                const name = document.getElementById('username-input').value.trim();
                if (name) {
                    localStorage.setItem('username', name);
                    currentUser = name;
                    document.getElementById('auth-modal').classList.add('hidden');
                }
            }

            // --- State Management ---
            let boardState = { cards: [], connections: [] };
            let activeLocks = {};
            let localLockId = null; 
            let heartbeatInterval = null;
            const canvas = document.getElementById('canvas');
            const svgLayer = document.getElementById('connections');
            let isDragging = false;
            const STAMP_LIBRARY = {
                'approved': '✅',
                'rejected': '❌',
                'urgent': '⚠️',
                'investigate': '🔍'
            };
            let dragOffset = { x: 0, y: 0 };

            async function queueAction(payload) {
                payload.user = currentUser || "Anonymous";
                await fetch('/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            // --- Subsystem C: Split-State Heartbeat Locking[cite: 1] ---
            function startHeartbeat(cardId) {
                if (localLockId !== cardId) {
                    localLockId = cardId;
                    queueAction({ action: "lock", card_id: cardId });
                    
                    if (heartbeatInterval) clearInterval(heartbeatInterval);
                    
                    heartbeatInterval = setInterval(() => {
                        queueAction({ action: "lock", card_id: cardId });
                    }, 5000); // Heartbeat ping payload every 5 seconds[cite: 1]
                }
            }

            function clearHeartbeat() {
                if (heartbeatInterval) clearInterval(heartbeatInterval);
                localLockId = null;
                heartbeatInterval = null;
            }

            // --- Subsystem D: Infinite Free-Form Canvas Layout[cite: 1] ---
            function renderBoard() {
                // Clear SVG lines
                svgLayer.innerHTML = '';
                
                // Track existing elements to avoid full DOM destruction
                const currentDOMIds = new Set(Array.from(canvas.children).map(el => el.id));
                const newIds = new Set(boardState.cards.map(c => c.id));
                
                // Remove deleted cards
                currentDOMIds.forEach(id => {
                    if (!newIds.has(id)) {
                        const el = document.getElementById(id);
                        if(el) el.remove();
                    }
                });

                // Render or update Cards
                boardState.cards.forEach(card => {
                    let cardEl = document.getElementById(card.id);
                    const isLockedByOther = activeLocks[card.id] && activeLocks[card.id].user !== currentUser;
                    
                    if (!cardEl) {
                        cardEl = document.createElement('div');
                        cardEl.id = card.id;
                        cardEl.className = 'card bg-yellow-100 shadow-lg border border-yellow-300 p-3 rounded shadow-[4px_4px_10px_rgba(0,0,0,0.3)] flex flex-col cursor-move';
                        
                        cardEl.innerHTML = `
                            <div class="flex justify-between items-start mb-1">
                                <input type="text" class="card-title font-bold text-sm bg-transparent border-none outline-none cursor-text w-full" placeholder="Title">
                                <div class="flex gap-2">
                                    <button class="stamp-btn text-slate-400 hover:text-green-500 text-xs font-bold cursor-pointer transition-colors" title="Add Stamp">⨁</button>
                                    <button class="delete-btn text-red-400 hover:text-red-600 text-xs font-bold cursor-pointer transition-colors">✕</button>
                                </div>
                            </div>
                            <textarea class="card-content text-xs cursor-text" placeholder="Write here..."></textarea>
                            <div class="text-[9px] text-slate-400 mt-auto text-right lock-status relative z-30"></div>
                            <div class="stamps-container absolute inset-0 pointer-events-none z-20 overflow-hidden rounded"></div>
                        `;

                        // Add Stamp Event Listener
                        const stampBtn = cardEl.querySelector('.stamp-btn');
                        stampBtn.addEventListener('mousedown', (e) => {
                            e.stopPropagation(); // Prevent drag logic
                            
                            // Pick a random stamp type for demonstration
                            const stampKeys = Object.keys(STAMP_LIBRARY);
                            const randomType = stampKeys[Math.floor(Math.random() * stampKeys.length)];
                            
                            queueAction({
                                action: "add_stamp",
                                card_id: card.id,
                                stamp_type: randomType,
                                // Drop the stamp at a random spot inside the card boundaries [cite: 22]
                                rel_x: Math.floor(Math.random() * 120),
                                rel_y: Math.floor(Math.random() * 120) + 20 
                            });
                        });

                        // [Keep your existing deleteBtn event listener here]
                        
                        // Attach the Deletion Event Listener
                        const deleteBtn = cardEl.querySelector('.delete-btn');
                        deleteBtn.addEventListener('mousedown', (e) => {
                            e.stopPropagation(); // Prevent the drag logic from triggering
                            if (confirm("Delete this card and its connections?")) {
                                queueAction({
                                    action: "delete_card",
                                    card_id: card.id
                                });
                            }
                        });
                        
                        canvas.appendChild(cardEl);
                        
                        // Dragging Logic
                        cardEl.addEventListener('mousedown', (e) => {
                            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                            if (activeLocks[card.id] && activeLocks[card.id].user !== currentUser) return; // Locked
                            
                            isDragging = true;
                            startHeartbeat(card.id);
                            
                            const rect = cardEl.getBoundingClientRect();
                            dragOffset.x = e.clientX - rect.left;
                            dragOffset.y = e.clientY - rect.top;
                            
                            document.addEventListener('mousemove', onMouseMove);
                            document.addEventListener('mouseup', onMouseUp);
                        });

                        const onMouseMove = (e) => {
                            if (!isDragging) return;
                            cardEl.style.left = (e.clientX - dragOffset.x) + 'px';
                            cardEl.style.top = (e.clientY - dragOffset.y) + 'px';
                            card.x = e.clientX - dragOffset.x;
                            card.y = e.clientY - dragOffset.y;
                            drawConnections(); // Dynamically redraw SVG lines on drag[cite: 1]
                        };

                        const onMouseUp = (e) => {
                            if (!isDragging) return;
                            isDragging = false;
                            document.removeEventListener('mousemove', onMouseMove);
                            document.removeEventListener('mouseup', onMouseUp);
                            
                            queueAction({
                                action: "move_card",
                                card_id: card.id,
                                x: parseInt(cardEl.style.left),
                                y: parseInt(cardEl.style.top)
                            });
                            clearHeartbeat();
                        };

                        // Editing logic
                        const titleInput = cardEl.querySelector('.card-title');
                        const contentInput = cardEl.querySelector('.card-content');
                        
                        const handleFocus = () => startHeartbeat(card.id);
                        const handleBlur = () => {
                            queueAction({
                                action: "edit_card",
                                card_id: card.id,
                                title: titleInput.value,
                                content: contentInput.value
                            });
                            clearHeartbeat();
                        };

                        titleInput.addEventListener('focus', handleFocus);
                        titleInput.addEventListener('blur', handleBlur);
                        contentInput.addEventListener('focus', handleFocus);
                        contentInput.addEventListener('blur', handleBlur);
                    }

                    // Update UI if we are NOT the ones currently locking/editing it
                    if (localLockId !== card.id) {
                        cardEl.style.left = card.x + 'px';
                        cardEl.style.top = card.y + 'px';
                        cardEl.querySelector('.card-title').value = card.title;
                        cardEl.querySelector('.card-content').value = card.content;
                    }

                    const stampsContainer = cardEl.querySelector('.stamps-container');
                    stampsContainer.innerHTML = ''; // Clear old stamps
                    if (card.stamps) {
                        card.stamps.forEach(stamp => {
                            const stampEl = document.createElement('div');
                            stampEl.className = 'absolute text-2xl drop-shadow-md transition-all select-none';
                            stampEl.style.left = stamp.rel_x + 'px';
                            stampEl.style.top = stamp.rel_y + 'px';
                            stampEl.innerHTML = STAMP_LIBRARY[stamp.type] || '❓';
                            stampsContainer.appendChild(stampEl);
                        });
                    }

                    // Handle lock indicator
                    const statusEl = cardEl.querySelector('.lock-status');
                    if (isLockedByOther) {
                        cardEl.style.opacity = '0.7';
                        cardEl.style.pointerEvents = 'none';
                        statusEl.innerText = `Locked by ${activeLocks[card.id].user}`;
                    } else {
                        cardEl.style.opacity = '1';
                        cardEl.style.pointerEvents = 'auto';
                        statusEl.innerText = card.last_edited_by ? `Last edit: ${card.last_edited_by}` : '';
                    }
                });

                drawConnections();
            }

            function drawConnections() {
                svgLayer.innerHTML = '';
                boardState.connections.forEach(conn => {
                    const fromCard = document.getElementById(conn.from_card_id);
                    const toCard = document.getElementById(conn.to_card_id);
                    
                    if (fromCard && toCard) {
                        // Calculate endpoints from absolute centers (x + 80, y + 80)[cite: 1]
                        const x1 = parseInt(fromCard.style.left) + 80;
                        const y1 = parseInt(fromCard.style.top) + 80;
                        const x2 = parseInt(toCard.style.left) + 80;
                        const y2 = parseInt(toCard.style.top) + 80;

                        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                        line.setAttribute('x1', x1);
                        line.setAttribute('y1', y1);
                        line.setAttribute('x2', x2);
                        line.setAttribute('y2', y2);
                        line.setAttribute('stroke', conn.color || 'red');
                        line.setAttribute('stroke-width', '4');
                        line.setAttribute('stroke-dasharray', '8,4');
                        
                        svgLayer.appendChild(line);
                    }
                });
            }

            function addCard() {
                const newId = 'card_' + Math.random().toString(36).substr(2, 9);
                queueAction({
                    action: "add_card",
                    card_id: newId,
                    title: "New Objective",
                    content: "",
                    x: Math.floor(Math.random() * 300) + 50,
                    y: Math.floor(Math.random() * 300) + 50
                });
            }

            // Sync Polling
            setInterval(async () => {
                try {
                    const res = await fetch('/state');
                    const data = await res.json();
                    boardState = data.state;
                    activeLocks = data.locks;
                    renderBoard();
                } catch (err) {
                    console.error("Sync error:", err);
                }
            }, 2000);

        </script>
    </body>
    </html>
    """