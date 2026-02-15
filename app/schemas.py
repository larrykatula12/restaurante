from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums para Pydantic
class RolEnum(str, Enum):
    admin = "admin"
    empleado = "empleado"

class EstadoPedidoEnum(str, Enum):
    abierto = "abierto"
    cerrado = "cerrado"
    cancelado = "cancelado"

class EstadoMesaEnum(str, Enum):
    libre = "libre"
    ocupada = "ocupada"
    reservada = "reservada"

class MetodoPagoEnum(str, Enum):
    efectivo = "efectivo"
    tarjeta = "tarjeta"
    transferencia = "transferencia"

# Usuarios
class UsuarioBase(BaseModel):
    nombre_completo: str
    email: EmailStr
    rol: RolEnum

class UsuarioCreate(UsuarioBase):
    contrasena: str  # Contraseña en texto plano, se hasheará

class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    email: Optional[EmailStr] = None
    contrasena: Optional[str] = None
    rol: Optional[RolEnum] = None
    activo: Optional[bool] = None

class UsuarioOut(UsuarioBase):
    id_usuario: int
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# Productos
class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    categoria: Optional[str] = None

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    categoria: Optional[str] = None
    activo: Optional[bool] = None

class ProductoOut(ProductoBase):
    id_producto: int
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# Mesas
class MesaBase(BaseModel):
    numero_mesa: int
    estado: EstadoMesaEnum = EstadoMesaEnum.libre

class MesaCreate(MesaBase):
    pass

class MesaUpdate(BaseModel):
    estado: Optional[EstadoMesaEnum] = None

class MesaOut(MesaBase):
    id_mesa: int

    class Config:
        from_attributes = True

# Detalle de pedido (para usar dentro de PedidoCreate)
class DetallePedidoBase(BaseModel):
    id_producto: int
    cantidad: int

class DetallePedidoOut(DetallePedidoBase):
    id_detalle: int
    precio_unitario: float
    subtotal: float

    class Config:
        from_attributes = True

# Pedidos
class PedidoBase(BaseModel):
    id_mesa: Optional[int] = None

class PedidoCreate(PedidoBase):
    detalles: List[DetallePedidoBase]  # Lista de productos con cantidad

class PedidoUpdate(BaseModel):
    id_mesa: Optional[int] = None
    estado: Optional[EstadoPedidoEnum] = None

class PedidoOut(PedidoBase):
    id_pedido: int
    id_usuario: int
    fecha_hora: datetime
    total: float
    estado: EstadoPedidoEnum
    detalles: List[DetallePedidoOut] = []
    pagos: List["PagoOut"] = []  # Se definirá después

    class Config:
        from_attributes = True

# Pagos
class PagoBase(BaseModel):
    metodo_pago: MetodoPagoEnum
    monto: float

class PagoCreate(PagoBase):
    id_pedido: int

class PagoOut(PagoBase):
    id_pago: int
    id_pedido: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

# Para resolver referencias circulares en PedidoOut
PedidoOut.model_rebuild()
PagoOut.model_rebuild()

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    rol: Optional[RolEnum] = None