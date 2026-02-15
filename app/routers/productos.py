from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, dependencies

router = APIRouter(prefix="/productos", tags=["Productos"])

# Ver todos los productos (activos)
@router.get("/", response_model=List[schemas.ProductoOut])
async def read_productos(skip: int = 0, limit: int = 100,
                         db: Session = Depends(dependencies.get_db),
                         current_user: models.Usuario = Depends(dependencies.get_current_user)):
    productos = db.query(models.Producto).filter(models.Producto.activo == True).offset(skip).limit(limit).all()
    return productos

# Ver un producto por ID
@router.get("/{producto_id}", response_model=schemas.ProductoOut)
async def read_producto(producto_id: int,
                        db: Session = Depends(dependencies.get_db),
                        current_user: models.Usuario = Depends(dependencies.get_current_user)):
    producto = db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()
    if not producto or not producto.activo:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

# Crear producto (solo admin)
@router.post("/", response_model=schemas.ProductoOut, status_code=status.HTTP_201_CREATED)
async def create_producto(producto: schemas.ProductoCreate,
                          db: Session = Depends(dependencies.get_db),
                          admin: models.Usuario = Depends(dependencies.get_current_admin)):
    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

# Actualizar producto (solo admin)
@router.put("/{producto_id}", response_model=schemas.ProductoOut)
async def update_producto(producto_id: int,
                          producto_update: schemas.ProductoUpdate,
                          db: Session = Depends(dependencies.get_db),
                          admin: models.Usuario = Depends(dependencies.get_current_admin)):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for field, value in producto_update.model_dump(exclude_unset=True).items():
        setattr(db_producto, field, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto

# Eliminar producto (solo admin) - borrado lógico (desactivar)
@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_producto(producto_id: int,
                          db: Session = Depends(dependencies.get_db),
                          admin: models.Usuario = Depends(dependencies.get_current_admin)):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db_producto.activo = False
    db.commit()
    return None