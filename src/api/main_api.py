from decouple import config
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel, create_engine, select
from datetime import datetime

from src.data.db_models import Event, User

app = FastAPI()

DATABASE_URL = config("PSQL_DATABASE_URL")
engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)


@app.get("/search_events/", response_model=list[Event])
def search_events(
	from_date: datetime | None = None,
	to_date: datetime | None = None,
	venue_keyword: str | None = None,
	category_keyword: str | None = None,
) -> list[Event]:
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
) -> list[Event]:
	"""
	Get all events.
	- **limit**: Maximum number of records to return.
	- **skip**: Amount of events skipped, query will pull the next 50 if available
	"""
	with Session(engine) as session:
		statement = select(Event).offset(skip).limit(limit)
		events = session.exec(statement).all()
		return events


@app.get("/events/{event_id}", response_model=Event)
def read_event(event_id: int) -> Event:
	with Session(engine) as session:
		event = session.get(Event, event_id)
		if not event:
			raise HTTPException(status_code=404, detail="Event not found")
	return event


@app.post("/events/", response_model=Event)
def create_event(event: Event) -> Event:
	with Session(engine) as session:
		session.add(event)
		session.commit()
		session.refresh(event)
	return event


@app.patch("/events/{event_id}", response_model=Event)
def update_event(event_id: int, event: Event) -> Event:
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


@app.post("/users/", response_model=User)
def create_user(user: User) -> User:
	with Session(engine) as session:
		session.add(user)
		session.commit()
		session.refresh(user)
	return user


@app.get("/user/", response_model=User)
def get_user(user_name) -> User:
	with Session(engine) as session:
		user = session.get(User, user_name)
		if not user:
			raise HTTPException(status_code=404, detail=f"User {user_name} not found")
	return user


@app.get("/users/", response_model=list[User])
def get_users(skip: int = 0, limit: int = 50) -> list[User]:
	"""
	Get all users.
	- **limit**: Maximum number of records to return.
	    - **skip**: Amount of events skipped, query will pull the next 50 if available
	"""
	with Session(engine) as session:
		statement = select(User).offset(skip).limit(limit)
		users = session.exec(statement).all()
		return users
