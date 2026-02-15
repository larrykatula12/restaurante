from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, usuarios, productos, pedidos
import os

# Crear las tablas en la base de datos (solo para desarrollo; en producción usar Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Punto de Venta", description="Backend para restaurante con roles", version="1.0.0")

# Configurar CORS para permitir peticiones desde el frontend (React)
origins = [
    "http://localhost:5173",  # Vite por defecto
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Por si acaso
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(productos.router)
app.include_router(pedidos.router)

@app.get("/")
def root():
    return {"message": "Bienvenido a la API del Restaurante"}