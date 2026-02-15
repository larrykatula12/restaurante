from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import models, schemas, dependencies

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# Crear pedido (empleado o admin)
@router.post("/", response_model=schemas.PedidoOut, status_code=status.HTTP_201_CREATED)
async def create_pedido(pedido: schemas.PedidoCreate,
                        db: Session = Depends(dependencies.get_db),
                        current_user: models.Usuario = Depends(dependencies.get_current_user)):
    # Crear cabecera del pedido
    db_pedido = models.Pedido(
        id_usuario=current_user.id_usuario,
        id_mesa=pedido.id_mesa,
        estado="abierto"
    )
    db.add(db_pedido)
    db.flush()  # Para obtener el id_pedido antes de commit

    # Procesar detalles
    total = 0.0
    for det in pedido.detalles:
        producto = db.query(models.Producto).filter(models.Producto.id_producto == det.id_producto).first()
        if not producto or not producto.activo:
            raise HTTPException(status_code=400, detail=f"Producto ID {det.id_producto} no disponible")
        precio = producto.precio
        subtotal = precio * det.cantidad
        total += subtotal
        db_detalle = models.DetallePedido(
            id_pedido=db_pedido.id_pedido,
            id_producto=det.id_producto,
            cantidad=det.cantidad,
            precio_unitario=precio,
        )
        db.add(db_detalle)

    db_pedido.total = total
    db.commit()
    db.refresh(db_pedido)

    # Devolver con relaciones (detalles)
    return db_pedido

# Listar pedidos (admin ve todos, empleado solo los suyos)
@router.get("/", response_model=List[schemas.PedidoOut])
async def read_pedidos(skip: int = 0, limit: int = 100,
                       db: Session = Depends(dependencies.get_db),
                       current_user: models.Usuario = Depends(dependencies.get_current_user)):
    query = db.query(models.Pedido).options(joinedload(models.Pedido.detalles), joinedload(models.Pedido.pagos))
    if current_user.rol != models.RolEnum.admin:
        query = query.filter(models.Pedido.id_usuario == current_user.id_usuario)
    pedidos = query.offset(skip).limit(limit).all()
    return pedidos

# Ver un pedido específico
@router.get("/{pedido_id}", response_model=schemas.PedidoOut)
async def read_pedido(pedido_id: int,
                      db: Session = Depends(dependencies.get_db),
                      current_user: models.Usuario = Depends(dependencies.get_current_user)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id_pedido == pedido_id)\
        .options(joinedload(models.Pedido.detalles), joinedload(models.Pedido.pagos)).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    # Empleado solo puede ver sus pedidos
    if current_user.rol != models.RolEnum.admin and pedido.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este pedido")
    return pedido

# Cerrar pedido (cambiar estado a cerrado) - el mismo empleado o admin
@router.put("/{pedido_id}/cerrar", response_model=schemas.PedidoOut)
async def cerrar_pedido(pedido_id: int,
                        db: Session = Depends(dependencies.get_db),
                        current_user: models.Usuario = Depends(dependencies.get_current_user)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id_pedido == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if current_user.rol != models.RolEnum.admin and pedido.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No puedes cerrar un pedido que no te pertenece")
    if pedido.estado != "abierto":
        raise HTTPException(status_code=400, detail="El pedido no está abierto")
    pedido.estado = "cerrado"
    db.commit()
    db.refresh(pedido)
    return pedido

# Agregar pago a un pedido (empleado o admin)
@router.post("/{pedido_id}/pagos", response_model=schemas.PagoOut, status_code=status.HTTP_201_CREATED)
async def create_pago(pedido_id: int,
                      pago: schemas.PagoCreate,
                      db: Session = Depends(dependencies.get_db),
                      current_user: models.Usuario = Depends(dependencies.get_current_user)):
    # Verificar que el pedido existe y pertenece al usuario si es empleado
    pedido = db.query(models.Pedido).filter(models.Pedido.id_pedido == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if current_user.rol != models.RolEnum.admin and pedido.id_usuario != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No puedes agregar pago a este pedido")
    if pedido.estado != "abierto":
        raise HTTPException(status_code=400, detail="No se pueden agregar pagos a un pedido cerrado o cancelado")

    db_pago = models.Pago(
        id_pedido=pedido_id,
        metodo_pago=pago.metodo_pago.value,
        monto=pago.monto
    )
    db.add(db_pago)
    # Opcional: actualizar total pagado? (lo dejamos simple)
    db.commit()
    db.refresh(db_pago)
    return db_pago