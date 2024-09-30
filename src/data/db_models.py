from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	title: str
	venue: str
	start_datetime: str
	category: str | None = None
	event_link: str | None = None
