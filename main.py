from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# â”€â”€ In-memory store (works on Vercel serverless) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_tasks: dict[int, dict] = {}
_next_id = 1

def _new_id() -> int:
    global _next_id
    i = _next_id
    _next_id += 1
    return i

# â”€â”€ Pydantic Models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False
    priority: str = Field("medium", pattern="^(low|medium|high)$")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    created_at: str
    updated_at: str

# â”€â”€ FastAPI App â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app = FastAPI(
    title="Yongskie Tasks API",
    description="Complete REST API for managing tasks â€” built by Manus-Claw for Yongskie ðŸ‡µðŸ‡­",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _task_to_response(t: dict) -> TaskResponse:
    return TaskResponse(**t)

def _get_or_404(task_id: int) -> dict:
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return _tasks[task_id]

# â”€â”€ Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Yongskie Tasks API â€” Live! ðŸš€",
        "author": "Yongskie from Philippines ðŸ‡µðŸ‡­",
        "built_by": "Manus-Claw AI Agent",
        "docs": "/docs",
        "endpoints": {
            "list":   "GET  /tasks",
            "get":    "GET  /tasks/{id}",
            "create": "POST /tasks",
            "update": "PUT  /tasks/{id}",
            "delete": "DELETE /tasks/{id}",
            "health": "GET  /health",
        },
    }

@app.get("/tasks", response_model=dict, tags=["Tasks"])
def list_tasks(
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """List all tasks with optional filters."""
    tasks = list(_tasks.values())
    if completed is not None:
        tasks = [t for t in tasks if t["completed"] == completed]
    if priority:
        tasks = [t for t in tasks if t["priority"] == priority]
    return {"tasks": tasks[skip:skip+limit], "total": len(tasks)}

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: int):
    """Get a task by ID."""
    return _task_to_response(_get_or_404(task_id))

@app.post("/tasks", response_model=TaskResponse, status_code=201, tags=["Tasks"])
def create_task(task: TaskCreate):
    """Create a new task."""
    now = datetime.utcnow().isoformat()
    tid = _new_id()
    record = {
        "id": tid,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "priority": task.priority,
        "created_at": now,
        "updated_at": now,
    }
    _tasks[tid] = record
    return _task_to_response(record)

@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(task_id: int, update: TaskUpdate):
    """Update an existing task."""
    record = _get_or_404(task_id)
    data = update.model_dump(exclude_unset=True)
    record.update(data)
    record["updated_at"] = datetime.utcnow().isoformat()
    return _task_to_response(record)

@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: int):
    """Delete a task."""
    _get_or_404(task_id)
    del _tasks[task_id]
    return {"message": f"Task {task_id} deleted", "id": task_id}

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "tasks_count": len(_tasks),
        "timestamp": datetime.utcnow().isoformat(),
    }
