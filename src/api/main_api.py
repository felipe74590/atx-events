from decouple import config
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel, create_engine, select
from typing import Optional
from datetime import datetime

from src.data.db_models import Event

app = FastAPI()

DATABASE_URL = config("PSQL_DATABASE_URL")
engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)


@app.get("/search_events/", response_model=list[Event])
def search_events(
	from_date: Optional[datetime] = None,
	to_date: Optional[datetime] = None,
	venue_keyword: Optional[str] = None,
	category_keyword: Optional[str] = None,
):
	"""
	Get a list of events based on specified search.
	- **limit**: Maximum number of records to return.
	- **from_date**: Filter events starting on this date
	- **to_date**: Filter events till this date
	- **venue_keyword**: Search for events in the venue name.
	"""
	with Session(engine) as session:
		statement = select(Event)

		if from_date is not None:
			statement = statement.where(Event.start_datetime >= from_date)
		if to_date is not None:
			statement = statement.where(Event.start_datetime <= to_date)
		# Will need improvement or seperate search call to get events by key words
		if venue_keyword is not None:
			statement = statement.where(Event.venue.ilike(f"%{venue_keyword}%"))
		if category_keyword is not None:
			statement = statement.where(Event.category.ilike(f"%{category_keyword}%"))

		events = session.exec(statement).all()
		return events


@app.get("/events/", response_model=list[Event])
def read_events(
	skip: int = 0,
	limit: int = 50,
):
	"""
	Get all events.
	- **limit**: Maximum number of records to return.
	- **skip**: Amount of events skipped, query will pull the next 50 if available
	"""
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


@app.patch("/events/{event_id}", response_model=Event)
def update_event(event_id: int, event: Event):
	with Session(engine) as session:
		db_event = session.get(Event, event_id)
		if not db_event:
			raise HTTPException(status_code=404, detail="Event not found")
		event_data = event.model_dump(exclude_uset=True)
		db_event.sqlmodel_update(event_data)
		event.id = event_id
		session.add(db_event)
		session.commit()
		session.refresh(db_event)
	return db_event


@app.delete("/events/{event_id}", response_model=Event)
def delete_event(event_id: int):
	with Session(engine) as session:
		event = session.get(Event, event_id)
		if not event:
			raise HTTPException(status_code=404, detail="Event not found")
		session.delete(event)
		session.commit()
	return event
