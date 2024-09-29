from decouple import config
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

from data.db_helper import Event

app = FastAPI()

DATABASE_URL = config("DATABASE")
engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)


@app.get("/events/", response_model=list[Event])
def read_events(skip: int = 0, limit: int = 20):
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


@app.get("/events/{event_id}", response_model=Event)
def read_event(event_id: int):
	with Session(engine) as session:
		event = session.get(Event, event_id)
		if not event:
			raise HTTPException(status_code=404, detail="Event not found")
	return event


@app.put("/events/{event_id}", response_model=Event)
def update_event(event_id: int, event: Event):
	with Session(engine) as session:
		db_event = session.get(Event, event_id)
		if not db_event:
			raise HTTPException(status_code=404, detail="Event not found")
		event.id = event_id
		session.merge(event)
		session.commit()
		session.refresh(event)
	return event


@app.delete("/events/{event_id}", response_model=Event)
def delete_event(event_id: int):
	with Session(engine) as session:
		event = session.get(Event, event_id)
		if not event:
			raise HTTPException(status_code=404, detail="Event not found")
		session.delete(event)
		session.commit()
	return event

