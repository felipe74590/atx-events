from sqlmodel import Field, SQLModel, Relationship
from typing import List


class UserEventsAttended(SQLModel, table=True):
	user_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
	event_id: int = Field(default=None, foreign_key="event.id", primary_key=True)


class UserEventsSaved(SQLModel, table=True):
	user_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
	event_id: int = Field(default=None, foreign_key="event.id", primary_key=True)


class Event(SQLModel, table=True):
	id: int | None = Field(default=None, primary_key=True)
	title: str
	venue: str
	start_datetime: str
	category: str | None = None
	event_link: str | None = None
	attendees: List["User"] = Relationship(back_populates="events_attended", link_model=UserEventsAttended)
	saved_by: List["User"] = Relationship(back_populates="events_saved", link_model=UserEventsSaved)


class UserBase(SQLModel):
	user_name: str
	email: str
	password: str


class User(UserBase, table=True):
	id: int | None = Field(default=None, primary_key=True)
	active: bool = True
	events_attended: List[Event] = Relationship(back_populates="attendees", link_model=UserEventsAttended)
	events_saved: List[Event] = Relationship(back_populates="saved_by", link_model=UserEventsSaved)
