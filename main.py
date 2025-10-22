from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

app = FastAPI()
engine = create_engine("sqlite:///games.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- DB MODELS ---
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    result = Column(String)
    totalScore = Column(Float)
    actions = relationship("Action", back_populates="game")
    events = relationship("Event", back_populates="game")

class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    actionType = Column(String)
    unitType = Column(String)
    round = Column(Integer)
    order = Column(Integer)
    game = relationship("Game", back_populates="actions")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    eventType = Column(String)
    unitType = Column(String)
    round = Column(Integer)
    order = Column(Integer)
    game = relationship("Game", back_populates="events")

Base.metadata.create_all(bind=engine)

# --- Pydantic MODELS ---
class GameSummary(BaseModel):
    result: str
    totalScore: float

class LoggedAction(BaseModel):
    actionType: str
    unitType: str
    round: int
    order: int

class LoggedEvent(BaseModel):
    eventType: str
    unitType: str
    round: int
    order: int

class GameLogPayload(BaseModel):
    game: GameSummary
    actions: List[LoggedAction]
    events: List[LoggedEvent]

# --- API ENDPOINT ---
@app.post("/match")
def save_match(payload: GameLogPayload):
    db = SessionLocal()
    game = Game(result=payload.game.result, totalScore=payload.game.totalScore)
    db.add(game)
    db.commit()
    db.refresh(game)

    for a in payload.actions:
        db.add(Action(
            game_id=game.id,
            actionType=a.actionType,
            unitType=a.unitType,
            round=a.round,
            order=a.order
        ))
    for e in payload.events:
        db.add(Event(
            game_id=game.id,
            eventType=e.eventType,
            unitType=e.unitType,
            round=e.round,
            order=e.order
        ))
    db.commit()
    return {"status": "ok", "gameId": game.id}
