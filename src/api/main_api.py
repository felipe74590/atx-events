from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel, create_engine, select
from datetime import datetime, timedelta
from src.data.db_helper import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
)
from src.constants import DATABASE_URL

from src.data.db_models import Event, User, Token, UserEventsAttended, UserEventsSaved

app = FastAPI()

engine = create_engine(DATABASE_URL)

SQLModel.metadata.create_all(engine)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = authenticate_user(session, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/events/attended", response_model=User)
def get_attended_events(current_user: User = Depends(get_current_active_user)):
    with Session(engine) as session:
        query = select(Event).where(UserEventsAttended.user_id == current_user.id)
        events = session.exec(query).all
        return events


@app.get("/users/me/events/saved", response_model=User)
def get_saved_events(current_user: User = Depends(get_current_active_user)):
    with Session(engine) as session:
        query = select(Event).where(UserEventsSaved.user_id == current_user.id)
        events = session.exec(query).all
        return events


@app.get("/users/me/", response_model=User)
def get_me(user: User = Depends(get_current_active_user)) -> User:
    with Session(engine) as session:
        user = session.get(User, user.user_name)
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User email {user.email} with username {user.user_name} not found"
            )
    return user


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
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")
    elif not from_date and to_date:
        raise HTTPException(status_code=400, detail="must provide a from_date if to_date is provided.")

    with Session(engine) as session:
        statement = select(Event)

        # Build the query filters
        filters = []
        if from_date is not None:
            filters.append(Event.start_datetime >= from_date)
        if to_date is not None:
            filters.append(Event.start_datetime <= to_date)
        if venue_keyword is not None:
            filters.append(Event.venue.ilike(f"%{venue_keyword}%"))
        if category_keyword is not None:
            filters.append(Event.category.ilike(f"%{category_keyword}%"))

        # Apply filters to the statement if there are any
        if filters:
            statement = statement.where(*filters)

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
        existing_user = session.exec(
            select(User).where(User.user_name == user.user_name, User.email == user.email)
        ).first()
        if existing_user is None:
            session.add(user)
            session.commit()
            session.refresh(user)
    return user


@app.get("/user/{user_id}", response_model=User)
def get_user(user: User) -> User:
    with Session(engine) as session:
        user = session.get(User, user.id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User id {user.id} with username {user.user_name} not found")
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
