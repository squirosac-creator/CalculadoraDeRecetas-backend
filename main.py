from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://squirosac-creator.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELOS
# =========================

class Ingrediente(BaseModel):
    nombre: str
    cantidad: float
    unidadEntrada: str
    unidadSalida: str


class RecetaRequest(BaseModel):
    invitados_originales: int
    invitados_nuevos: int
    ingredientes: List[Ingrediente]


# =========================
# FACTORES DE CONVERSIÓN
# =========================

FACTORES = {
    "g": {"g": 1, "kg": 0.001},
    "kg": {"g": 1000, "kg": 1},
    "ml": {"ml": 1, "l": 0.001},
    "l": {"ml": 1000, "l": 1},
}

# =========================
# UTILIDADES
# =========================

def conversion_valida(origen: str, destino: str) -> bool:
    return origen in FACTORES and destino in FACTORES[origen]


def convertir(cantidad: float, origen: str, destino: str) -> float:
    return cantidad * FACTORES[origen][destino]


# =========================
# ENDPOINT
# =========================

@app.post("/ajustar-receta")
def ajustar_receta(data: RecetaRequest):
    if data.invitados_originales <= 0 or data.invitados_nuevos <= 0:
        raise HTTPException(status_code=400, detail="Cantidad de invitados inválida")

    factor = data.invitados_nuevos / data.invitados_originales
    ingredientes_ajustados = []

    for ing in data.ingredientes:
        # 1️⃣ validar conversión
        if not conversion_valida(ing.unidadEntrada, ing.unidadSalida):
            raise HTTPException(
                status_code=400,
                detail=f"No existe conversión válida entre {ing.unidadEntrada} y {ing.unidadSalida}"
            )

        # 2️⃣ aplicar proporción
        cantidad_ajustada = ing.cantidad * factor

        # 3️⃣ convertir unidad
        cantidad_convertida = convertir(
            cantidad_ajustada,
            ing.unidadEntrada,
            ing.unidadSalida
        )

        ingredientes_ajustados.append({
            "nombre": ing.nombre,
            "cantidad": round(cantidad_convertida, 2),
            "unidad": ing.unidadSalida
        })

    return {
        "factor": round(factor, 2),
        "ingredientes": ingredientes_ajustados
    }
