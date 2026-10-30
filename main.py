from fastapi import FastAPI, Depends, HTTPException, Query
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import models
from models import Users, Books, Reservations, IssueRecords
from database import engine, SessionLocal
from fastapi.responses import JSONResponse
from router import admin, auth
from router.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(admin.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


#get all books route
@app.get('/books/all')
def get_all_books(db: db_dependency):
    
    books = db.query(Books).all()
    return books


@app.get('/books/{book_id}')
def get_specific_books(user: user_dependency, db: db_dependency, book_id: int):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    book = db.query(Books).filter(Books.id == book_id).first()
    
    if book is None:
        raise HTTPException(status_code=404, detail='Book not found')
    return book


@app.post('/reserve/{book_id}')
def reserve_book(user: user_dependency, db: db_dependency, book_id: int):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    book = db.query(Books).filter(Books.id == book_id).first()
        
    if book is None:
        raise HTTPException(status_code=404, detail='Book not found')
    
    reservation_model = Reservations(
        book_id = book_id,
        user_id = user.get('id'),
        status = 'pending'
    )
    
    db.add(reservation_model)
    db.commit()
    
    return JSONResponse(status_code=201, content={'message': 'Book reserved'})


@app.delete('/reserve/cancel/{reservation_id}')
def cancel_reservation(user: user_dependency, db: db_dependency, reservation_id: int):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    reservation = db.query(Reservations).filter(Reservations.id == reservation_id).first()
        
    if reservation is None:
        raise HTTPException(status_code=404, detail='Reservation not found')
    
    reservation.status = 'cancelled'
    db.commit()
    
    return JSONResponse(status_code=201, content={'message': 'Reservation cancelled successfully'})


@app.get('/reserve/my')
def my_reservation(user: user_dependency, db: db_dependency):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    reservations = db.query(Reservations).filter(Reservations.user_id == user.get('id')).all()
        
    if reservations is None:
        raise HTTPException(status_code=404, detail='No reservation created yet')
    
    return reservations


@app.get('/issues/my')
def my_issued_books(user: user_dependency, db: db_dependency):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    issues = db.query(IssueRecords).filter(IssueRecords.user_id == user.get('id')).all()
        
    if issues is None:
        raise HTTPException(status_code=404, detail='No issued books found')
    
    return issues



@app.get('/user_profile')
def get_user_profile(user : user_dependency, db : db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail="User didnot loged in yet!!!")
    
    return db.query(Users).filter(Users.id == user.get('id')).first()