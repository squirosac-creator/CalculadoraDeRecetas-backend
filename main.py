# /** @format */

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
# UNIDADES (BASE)
# =========================

# FACTORES hacia unidad base
# masa → gramos
# volumen → ml
FACTORES = {
    # MASA
    "g": 1,
    "kg": 1000,
    "mg": 0.001,
    "oz": 28.3495,
    "lb": 453.592,

    # VOLUMEN
    "ml": 1,
    "l": 1000,
    "tsp": 5,        # cucharadita
    "tbsp": 15,      # cucharada
    "cup": 240,      # taza
    "dash": 0.6,     # pizca líquida aprox
    "pinch": 0.3,    # pizca seca aprox
}

# tipo de unidad (para evitar conversiones inválidas)
TIPO_UNIDAD = {
    # masa
    "g": "masa",
    "kg": "masa",
    "mg": "masa",
    "oz": "masa",
    "lb": "masa",

    # volumen
    "ml": "volumen",
    "l": "volumen",
    "tsp": "volumen",
    "tbsp": "volumen",
    "cup": "volumen",
    "dash": "volumen",
    "pinch": "volumen",
}

# =========================
# UTILIDADES
# =========================

def conversion_valida(origen: str, destino: str) -> bool:
    return (
        origen in FACTORES
        and destino in FACTORES
        and TIPO_UNIDAD[origen] == TIPO_UNIDAD[destino]
    )


def convertir(cantidad: float, origen: str, destino: str) -> float:
    # 1️⃣ convertir a unidad base
    base = cantidad * FACTORES[origen]

    # 2️⃣ convertir a unidad destino
    return base / FACTORES[destino]


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

        # validar existencia de unidades
        if ing.unidadEntrada not in FACTORES or ing.unidadSalida not in FACTORES:
            raise HTTPException(
                status_code=400,
                detail=f"Unidad no soportada: {ing.unidadEntrada} o {ing.unidadSalida}"
            )

        # validar tipo compatible
        if not conversion_valida(ing.unidadEntrada, ing.unidadSalida):
            raise HTTPException(
                status_code=400,
                detail=f"No se puede convertir de {ing.unidadEntrada} a {ing.unidadSalida}"
            )

        # aplicar proporción
        cantidad_ajustada = ing.cantidad * factor

        # convertir
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
