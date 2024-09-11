from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    venue: str
    start_datetime: str
    category: Optional[str] = None
    event_link: Optional[str] = None


sqlite_file_name = "atx_events.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)
SQLModel.metadata.create_all(engine)


def add_events_to_db(events):

    with Session(engine) as session:
        # check if events already exsits based on title and start_datetime
        for event in events:
            existing_event = session.exec(
                select(Event).where(
                    Event.title == event["title"],
                    Event.start_datetime == event["start_datetime"],
                )
            ).first()

            if not existing_event:
                new_event = Event(**event)
                session.add(new_event)
        session.commit()
