from decouple import config
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.data.db_models import Event
import sqlite3

sqlite_url = config("LITE_DATABASE")
sqlite_db_name = config("SQLITE_DB")

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
				print(f"This event {event.title} on {event.start_datetime} already exists in database")
		print(f"A total of {events_added} Events were added to the database.")

		session.commit()


postgresql_url = config("PSQL_MIRGRATE_URL")


async def migrate_to_postgresql():
	"""Migrate data in sqlite databse atx_events to postgreSQL database atx-events"""
	sqlite_conn = sqlite3.connect(sqlite_db_name)
	sqlite_cursor = sqlite_conn.cursor()

	# Connect to PostgreSQL, connect tables
	postgres_engine = create_async_engine(postgresql_url, echo=True)
	async_session = sessionmaker(postgres_engine, class_=AsyncSession, expire_on_commit=False)

	async with postgres_engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.create_all)

	sqlite_cursor.execute("SELECT * FROM event")
	rows = sqlite_cursor.fetchall()

	async with async_session() as session:
		for row in rows:
			existing_event = await session.execute(select(Event).where(Event.id == row[0]))
			if not existing_event:
				event_instance = Event(
					id=row[0], title=row[1], venue=row[2], start_datetime=row[3], category=row[4], event_link=row[5]
				)
				session.add(event_instance)
		await session.commit()
	sqlite_conn.close()


# if __name__ == "__main__":
# 	asyncio.run(migrate_to_postgresql())
