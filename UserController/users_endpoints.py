# auth_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from db import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from AuthController.auth_dependencies import get_current_user
from DataModels.UserModel import User
from Schemas.UserSchema import UserResponse, UserCreate, UserUpdate



router = APIRouter(prefix="/users", tags=["Users"])
bearer = HTTPBearer(auto_error=True)


#GET CURRENT USER ENDPOINT
@router.get("/me", tags=["Users"], response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


#GET USER BY ID ENDPOINT
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


#CREATE USER ENDPOINT
@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    #admin only
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    # Check duplicate email
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    #check duplicate username
    resultusername = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_username = resultusername.scalar_one_or_none()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password, #will need to change for password hashing
        is_admin=user_data.is_admin,
        is_active=user_data.is_active,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user



#PATCH USER UPDATE ENDPOINT
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    #non-admins can only edit themselves
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Load target user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Block is_admin updates unless caller is admin
    if payload.is_admin is not None and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can change is_admin")

    # If updating email, ensure unique
    if payload.email is not None and payload.email != user.email:
        res = await db.execute(select(User).where(User.email == payload.email))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = payload.email

    # If updating username, ensure unique
    if payload.username is not None and payload.username != user.username:
        res = await db.execute(select(User).where(User.username == payload.username))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = payload.username

    # Update is_active if provided
    if payload.is_active is not None:
        user.is_active = payload.is_active

    # Update password (TEMP: no hashing, per your earlier choice)
    if payload.password is not None:
        if hasattr(user, "password_hash"):
            user.password_hash = payload.password
        else:
            user.password = payload.password

    # Update is_admin only if allowed
    if payload.is_admin is not None and current_user.is_admin:
        user.is_admin = payload.is_admin

    await db.commit()
    await db.refresh(user)
    return user