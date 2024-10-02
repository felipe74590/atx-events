from decouple import config
from sqlmodel import Session, SQLModel, create_engine, select
from src.data.db_models import Event

db_url = config("PSQL_DATABASE_URL")

engine = create_engine(db_url)
SQLModel.metadata.create_all(engine)


def add_events_to_db(events):
	events_added = 0
	with Session(engine) as session:
		# check if events already exsits based on title and start_datetime
		for event in events:
			existing_event = session.exec(
				select(Event).where(
					Event.title == event.title,
					Event.start_datetime == event.start_datetime,
				)
			).first()

			if existing_event is None:
				new_event = Event(
					**event._asdict(),
				)
				session.add(new_event)
				events_added += 1

			else:
				print(f"This event {event.title} on {event.start_datetime} already exists in database")
		print(f"A total of {events_added} Events were added to the database.")

		session.commit()
