from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from sqlalchemy import inspect

from config import DEFAULT_SETTINGS
from crud_models import UserCreate, UserResponse, UserUpdate
from db import get_db, Base, engine
from db_actions import get_user, create_user, get_users, update_user, delete_user
from security import manager, verify_password
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 添加CORSMiddleware中间件，配置允许的源、方法等
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许的方法
    allow_headers=["*"],  # 允许的头部
)

@app.on_event("startup")
def setup():
    print("Creating db tables...")
    Base.metadata.create_all(bind=engine)
    inspection = inspect(engine)
    print(f"Created {len(inspection.get_table_names())} tables: {inspection.get_table_names()}")


@app.post("/auth/register")
def register(user: UserCreate, db=Depends(get_db)):
    if get_user(user.email) is not None:
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    else:
        db_user = create_user(db, user)
        return UserResponse(id=db_user.id, email=db_user.email, is_admin=db_user.is_admin)


@app.post(DEFAULT_SETTINGS.token_url)
def token_login(data: OAuth2PasswordRequestForm = Depends()):
    email = data.username
    password = data.password

    user = get_user(email)  # we are using the same function to retrieve the user
    if user is None:
        raise InvalidCredentialsException  # you can also use your own HTTPException
    elif not verify_password(password, user.password):
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data=dict(sub=user.email)
    )
    return {'access_token': access_token, 'token_type': 'Bearer'}


@app.post("/users/login")
async def login(request: Request):
    data = await request.json()
    email = data['username']
    password = data['password']
    # 打印日志记录入参
    logging.info(f"Login attempt with username: {email}")
    
    user = get_user(email)  # 我们使用相同的函数来检索用户
    if user is None:
        raise HTTPException(status_code=402, detail="无效的邮箱或密码")
    elif not verify_password(password, user.password):
        raise HTTPException(status_code=402, detail="无效的邮箱或密码")

    access_token = manager.create_access_token(
        data=dict(sub=user.email)
    )
    return {"data": {"token": access_token}, "code": 0, "message": "登录成功"}


@app.get("/users/info")
async def user_info(user=Depends(manager)):
    # return {"code": 0, "data": user, "message": "获取用户详情成功"}
    if user.is_admin:
        return {"code": 0, "data": {"username": user.email, "roles": ["admin"]}, "message": "获取用户详情成功"}
    else:
        return {"code": 0, "data": {"username": user.email, "roles": ["editor"]}, "message": "获取用户详情成功"}

@app.get("/private")
def private_route(user=Depends(manager)):
    return {"detail": f"Welcome {user.email}"}


@app.post("/member")
async def create_member(request: Request, db=Depends(get_db)):
    data = await request.json()
    email = data['username']
    password = data['password']
    if get_user(email) is not None:
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    else:
        user_data = UserCreate(email=email, password=password)
        db_user = create_user(db, user_data)
        return {"code": 0, "data": {"id": db_user.id, "email": db_user.email, "is_admin": db_user.is_admin}}

@app.delete("/member/{id}")
def delete_member(id: int, db=Depends(get_db)):
    # 实现删除用户的逻辑
    delete_result = delete_user(db, id)  # 假设实现了 delete_user 函数
    if not delete_result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@app.put("/member")
def update_member(user_update: UserUpdate, db=Depends(get_db)):  # 假设UserUpdate是更新用户信息的模型
    # 实现更新用户的逻辑
    updated_user = update_user(db, user_update)  # 假设实现了 update_user 函数
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully", "user": updated_user}

@app.get("/member")
def get_members(query: str = None, db=Depends(get_db)):
    # 实现获取用户数据的逻辑
    users = get_users(db, query)  # 假设实现了 get_users 函数
    return {"code": 0, "data": users}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000)
