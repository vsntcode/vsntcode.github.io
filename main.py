from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to restrict origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

class Topics(BaseModel):
    topics: List[str]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/questions/{question_id}")
async def read_question(question_id: int, db: db_dependency):
    result = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail='Question is not found')
    return result

@app.get("/choices/{question_id}")
async def read_choices(question_id: int, db: db_dependency):
    result = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not result:
        raise HTTPException(status_code=404, detail='Choices are not found')
    return result

@app.post("/questions/")
async def create_questions(question: QuestionBase, db: db_dependency): 
    db_question = models.Questions(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=db_question.id)
        db.add(db_choice)
    db.commit()
    return {"question_id": db_question.id}

@app.put("/questions/{question_id}")
async def update_question(question_id: int, question: QuestionBase, db: db_dependency):
    db_question = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')
    db_question.question_text = question.question_text
    db.query(models.Choices).filter(models.Choices.question_id == question_id).delete()
    for choice in question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=question_id)
        db.add(db_choice)
    db.commit()
    return {"message": "Question updated successfully"}

@app.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: db_dependency):
    db_question = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')
    db.query(models.Choices).filter(models.Choices.question_id == question_id).delete()
    db.delete(db_question)
    db.commit()
    return {"message": "Question deleted successfully"}

@app.get("/questions/")
async def read_all_questions(db: db_dependency):
    questions = db.query(models.Questions).all()
    return [{"id": question.id, "question_text": question.question_text} for question in questions]

@app.get("/topics/", response_model=Topics)
async def get_topics():
    topics = [
        "Robyn",
        "FastAPI",
        "List",
        "Tuples",
        "Dict",
        "Class",
        "Functions",
        "File Handling",
        "Connectivity from Python",
        "Venv",
        "JSON",
        "Requests",
        "PostgreSQL",
        "GIT",
        "__init__",
        "__str__"
    ]
    return {"topics": topics}