from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from bot_service import BotService

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize bot service
bot_service = BotService()

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Wallet(BaseModel):
    address: str
    name: Optional[str] = None

class BotSettings(BaseModel):
    max_sol_per_tx: float
    slippage: float
    delay_ms: int
    blacklisted_tokens: List[str]

class BotState(BaseModel):
    is_running: bool
    tracked_wallets: List[Wallet]
    settings: BotSettings

# Fake user database
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("supersecret"),
        "disabled": False,
    }
}

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/state", response_model=BotState)
async def get_state(current_user: User = Depends(get_current_active_user)):
    status = await bot_service.get_status()
    return BotState(
        is_running=status["is_running"],
        tracked_wallets=[Wallet(address=addr) for addr in status["tracked_wallets"]],
        settings=BotSettings(**status["settings"])
    )

@app.post("/wallets")
async def add_wallet(wallet: Wallet, current_user: User = Depends(get_current_active_user)):
    if wallet.address in bot_service.tracked_wallets:
        raise HTTPException(status_code=400, detail="Wallet already tracked")
    bot_service.tracked_wallets.append(wallet.address)
    return {"status": "success"}

@app.delete("/wallets/{address}")
async def remove_wallet(address: str, current_user: User = Depends(get_current_active_user)):
    if address not in bot_service.tracked_wallets:
        raise HTTPException(status_code=404, detail="Wallet not found")
    bot_service.tracked_wallets.remove(address)
    return {"status": "success"}

@app.post("/start-bot")
async def start_bot(current_user: User = Depends(get_current_active_user)):
    result = await bot_service.start()
    return result

@app.post("/stop-bot")
async def stop_bot(current_user: User = Depends(get_current_active_user)):
    result = await bot_service.stop()
    return result

@app.get("/status")
async def get_bot_status(current_user: User = Depends(get_current_active_user)):
    return await bot_service.get_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 