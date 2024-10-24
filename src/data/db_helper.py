from sqlmodel import Session, SQLModel, create_engine, select
from src.data.db_models import Event, User, TokenData
from src.constants import DATABASE_URL, SECRET_KEY
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext


engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


### AUTHENTICATION
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_username(session, username: str):
    query = select(User).where(User.user_name == username)
    user = session.exec(query).first()
    return user


def authenticate_user(session, username: str, password: str):
    query = select(User).where(User.user_name == username)
    user = session.exec(query).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user_by_username(session, username=token_data.username)

    if user is None:
        raise credential_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


### ADDING EVENTS TO DB FROM WEBSCRAPERS
def add_events_to_db(events):
    events_added = 0
    # check if events already exsits based on title and start_datetime
    with Session(engine) as session:
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
