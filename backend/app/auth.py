from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import jwt,JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
SECRET='smart-warehouse-demo-secret'; ALGO='HS256'; crypt=CryptContext(schemes=['bcrypt'],deprecated='auto'); bearer=HTTPBearer()
def hash_password(v): return crypt.hash(v)
def verify(v,h): return crypt.verify(v,h)
def token(user): return jwt.encode({'sub':str(user.id),'role':user.role.name},SECRET,algorithm=ALGO)
def current(c:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
 try: uid=int(jwt.decode(c.credentials,SECRET,algorithms=[ALGO])['sub'])
 except (JWTError,ValueError): raise HTTPException(401,'Invalid token')
 u=db.get(User,uid)
 if not u: raise HTTPException(401,'User missing')
 return u
def roles(*allowed):
 def guard(u=Depends(current)):
  if u.role.name not in allowed: raise HTTPException(status.HTTP_403_FORBIDDEN,'Owner permission required')
  return u
 return guard
