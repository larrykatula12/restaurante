from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth, dependencies

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Obtener todos los usuarios (solo admin)
@router.get("/", response_model=List[schemas.UsuarioOut])
async def read_usuarios(skip: int = 0, limit: int = 100,
                        db: Session = Depends(dependencies.get_db),
                        current_user: models.Usuario = Depends(dependencies.get_current_admin)):
    usuarios = db.query(models.Usuario).offset(skip).limit(limit).all()
    return usuarios

# Obtener un usuario por ID (solo admin o el mismo usuario)
@router.get("/{usuario_id}", response_model=schemas.UsuarioOut)
async def read_usuario(usuario_id: int,
                       db: Session = Depends(dependencies.get_db),
                       current_user: models.Usuario = Depends(dependencies.get_current_user)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # Si no es admin, solo puede verse a sí mismo
    if current_user.rol != models.RolEnum.admin and current_user.id_usuario != usuario_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este usuario")
    return usuario

# Crear usuario (solo admin)
@router.post("/", response_model=schemas.UsuarioOut, status_code=status.HTTP_201_CREATED)
async def create_usuario(usuario: schemas.UsuarioCreate,
                         db: Session = Depends(dependencies.get_db),
                         current_user: models.Usuario = Depends(dependencies.get_current_admin)):
    # Verificar si ya existe el email
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear nuevo usuario con contraseña hasheada
    hashed_password = auth.get_password_hash(usuario.contrasena)
    db_usuario = models.Usuario(
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        contrasena_hash=hashed_password,
        rol=usuario.rol.value
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# Actualizar usuario (solo admin o el mismo usuario)
@router.put("/{usuario_id}", response_model=schemas.UsuarioOut)
async def update_usuario(usuario_id: int,
                         usuario_update: schemas.UsuarioUpdate,
                         db: Session = Depends(dependencies.get_db),
                         current_user: models.Usuario = Depends(dependencies.get_current_user)):
    # Obtener usuario a modificar
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Permisos: admin puede modificar cualquiera; usuario común solo a sí mismo
    if current_user.rol != models.RolEnum.admin and current_user.id_usuario != usuario_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este usuario")
    
    # Si se intenta cambiar el rol, solo admin puede hacerlo
    if usuario_update.rol is not None and current_user.rol != models.RolEnum.admin:
        raise HTTPException(status_code=403, detail="Solo un administrador puede cambiar el rol")
    
    # Actualizar campos
    if usuario_update.nombre_completo is not None:
        db_usuario.nombre_completo = usuario_update.nombre_completo
    if usuario_update.email is not None:
        # Verificar que el nuevo email no esté ocupado por otro usuario
        existing = db.query(models.Usuario).filter(models.Usuario.email == usuario_update.email).first()
        if existing and existing.id_usuario != usuario_id:
            raise HTTPException(status_code=400, detail="El email ya está en uso")
        db_usuario.email = usuario_update.email
    if usuario_update.contrasena is not None:
        db_usuario.contrasena_hash = auth.get_password_hash(usuario_update.contrasena)
    if usuario_update.rol is not None:
        db_usuario.rol = usuario_update.rol.value
    if usuario_update.activo is not None:
        db_usuario.activo = usuario_update.activo

    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# Eliminar usuario (solo admin)
@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(usuario_id: int,
                         db: Session = Depends(dependencies.get_db),
                         current_user: models.Usuario = Depends(dependencies.get_current_admin)):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # Opcional: en lugar de borrar, se puede desactivar
    db.delete(db_usuario)
    db.commit()
    return None