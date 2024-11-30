from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

class Event(BaseModel):
    name: str
    date: str
    description: str = None

def create_connection():
    return sqlite3.connect('events.db')

@app.post("/create_events/")
def create_event(event: Event):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (name, date, description) VALUES (?, ?, ?)",
                   (event.name, event.date, event.description))
    conn.commit()
    conn.close()
    return {"message": "Мероприятие создано"}

@app.get("/view_events/")
def read_events():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    
    result = {}
    for t in events:
        # Используем первый элемент кортежа как ключ
        key = t[0]
        # Создаем подсловарь для значения
        value = {
            'name': t[1],       
            'date': t[2],
            'description': t[3] 
        }
        # Добавляем в основной словарь
        result[key] = value
        
    return result

@app.get("/last_event/")
def read_last_event():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT 1")
    last_event = cursor.fetchone()
    conn.close()

    if last_event:
        # Предполагается, что ваша таблица имеет следующие столбцы
        result = {
            'name': last_event[1],
            'date': last_event[2],
            'description': last_event[3]
        }
        return result
    else:
        return {"error": "No events found."}

@app.put("/events/{event_id}")
def update_event(event_id: int, event: Event):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE events SET name = ?, date = ?, description = ? WHERE id = ?",
                   (event.name, event.date, event.description, event_id))
    conn.commit()
    conn.close()
    return {"message": "Event updated successfully"}

@app.delete("/close_events/{event_name}")
def delete_event(event_name: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE name = ?", (event_name,))
    conn.commit()
    conn.close()
    return {"message": "Мероприятие удалено"}