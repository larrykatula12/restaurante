from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class RolEnum(str, enum.Enum):
    admin = "admin"
    empleado = "empleado"

class EstadoPedidoEnum(str, enum.Enum):
    abierto = "abierto"
    cerrado = "cerrado"
    cancelado = "cancelado"

class EstadoMesaEnum(str, enum.Enum):
    libre = "libre"
    ocupada = "ocupada"
    reservada = "reservada"

class MetodoPagoEnum(str, enum.Enum):
    efectivo = "efectivo"
    tarjeta = "tarjeta"
    transferencia = "transferencia"

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(Enum(RolEnum), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    pedidos = relationship("Pedido", back_populates="usuario")

class Producto(Base):
    __tablename__ = "productos"

    id_producto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float, nullable=False)
    categoria = Column(String(50))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    detalles = relationship("DetallePedido", back_populates="producto")

class Mesa(Base):
    __tablename__ = "mesas"

    id_mesa = Column(Integer, primary_key=True, index=True)
    numero_mesa = Column(Integer, unique=True, nullable=False)
    estado = Column(Enum(EstadoMesaEnum), default="libre")

    pedidos = relationship("Pedido", back_populates="mesa")

class Pedido(Base):
    __tablenante__ = "pedidos"

    id_pedido = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_mesa = Column(Integer, ForeignKey("mesas.id_mesa"))
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now())
    total = Column(Float, default=0.0)
    estado = Column(Enum(EstadoPedidoEnum), default="abierto")

    usuario = relationship("Usuario", back_populates="pedidos")
    mesa = relationship("Mesa", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="pedido")

class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id_detalle = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, computed="cantidad * precio_unitario")  # Opcional, se puede calcular

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")

class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"), nullable=False)
    metodo_pago = Column(Enum(MetodoPagoEnum), nullable=False)
    monto = Column(Float, nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now())

    pedido = relationship("Pedido", back_populates="pagos")