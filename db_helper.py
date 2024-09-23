from decouple import config
from sqlmodel import Field, Session, SQLModel, create_engine, select

sqlite_file_name = config("DATABASE")
sqlite_url = f"sqlite:///{sqlite_file_name}"


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    venue: str
    start_datetime: str
    category: str | None = None
    event_link: str | None = None


engine = create_engine(sqlite_url)
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
                print(
                    f"This event {event.title} on {event.start_datetime} already exists in database"
                )
        print(f"A total of {events_added} Events were added to the database.")

        session.commit()
