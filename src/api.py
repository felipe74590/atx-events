import uvicorn
from decouple import config
from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine, select

from db_helper import Event

app = FastAPI()

DATABASE_URL = config("DATABASE")
engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)

@app.get("/events/", response_model=list[Event])
def read_events(skip:int=0, limit: int = 20):
    with Session(engine) as session:
        statement = select(Event).offset(skip).limit(limit)
        events = session.exec(statement).all()
        return events

@app.post("/events/", response_model=Event)
def create_event(event: Event):
    with Session(engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)
    return event

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=800)
