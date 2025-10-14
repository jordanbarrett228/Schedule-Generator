# backend/app/routers/auth_rt.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from ..auth import users_engine, verify_password, create_access_token, create_users_db_and_tables
from ..models.user import User, UserRead

router = APIRouter()

# Ensure users DB exists
create_users_db_and_tables()

@router.post("/api/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # form_data.username and .password
    with Session(users_engine) as session:
        stmt = select(User).where(User.username == form_data.username)
        user = session.exec(stmt).first()
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        if not verify_password(form_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        access_token = create_access_token(subject=user.username)
        return {"access_token": access_token, "token_type": "bearer"}

from ..auth import get_current_user as _get_current_user

@router.get("/api/me", response_model=UserRead, dependencies=[Depends(_get_current_user)])
def read_current_user(current_user: UserRead = Depends(_get_current_user)):
    return current_user
