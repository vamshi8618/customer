from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

tasks = []

class Task(BaseModel):
    title: str

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks

@app.post("/tasks")
def add_task(task: Task):
    tasks.append(task)
    return {"message": "Task added successfully"}

@app.delete("/tasks/{task_index}")
def delete_task(task_index: int):
    if 0 <= task_index < len(tasks):
        tasks.pop(task_index)
        return {"message": "Task deleted successfully"}
    return {"error": "Invalid task index"}
