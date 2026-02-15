from .database import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . import auth, models, schemas
from sqlalchemy.orm import Session

# Dependencia para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esquema de autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Obtener usuario actual a partir del token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = auth.verify_token(token, credentials_exception)
    user = db.query(models.Usuario).filter(models.Usuario.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return user

# Dependencia para verificar si el usuario es administrador
async def get_current_admin(current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != models.RolEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos de administrador")
    return current_user