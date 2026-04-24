# =========================
# IMPORTS
# =========================

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Creamos la API
app = FastAPI()

# =========================
# CORS (conexión frontend-backend)
# =========================
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

# =========================================================
# MODELOS (estructura de datos que recibe el backend)
# =========================================================

class Ingrediente(BaseModel):
    nombre: str
    cantidad: float
    unidadEntrada: str
    unidadSalida: str


class RecetaRequest(BaseModel):
    invitados_originales: int
    invitados_nuevos: int
    ingredientes: List[Ingrediente]


# =========================================================
# CONSTANTES MATEMÁTICAS: FACTORES DE CONVERSIÓN
# =========================================================
"""
🔢 AQUÍ HAY MATEMÁTICA DE CONVERSIÓN DE UNIDADES

Cada unidad se expresa en una unidad base:
- masa → gramos
- volumen → mililitros

Esto permite convertir usando una regla:
    valor_en_base = cantidad × factor
    valor_final = valor_base ÷ factor_destino
"""

FACTORES = {
    # MASA (todo se convierte a gramos)
    "g": 1,
    "kg": 1000,
    "mg": 0.001,
    "oz": 28.3495,
    "lb": 453.592,

    # VOLUMEN (todo se convierte a ml)
    "ml": 1,
    "l": 1000,
    "tsp": 5,
    "tbsp": 15,
    "cup": 240,
    "dash": 0.6,
    "pinch": 0.3,
}

# =========================================================
# CLASIFICACIÓN DE UNIDADES (para evitar errores matemáticos)
# =========================================================
"""
🔍 IMPORTANTE:
Esto evita conversiones inválidas como:
    gramos ↔ mililitros (masa ≠ volumen)
"""

TIPO_UNIDAD = {
    "g": "masa",
    "kg": "masa",
    "mg": "masa",
    "oz": "masa",
    "lb": "masa",

    "ml": "volumen",
    "l": "volumen",
    "tsp": "volumen",
    "tbsp": "volumen",
    "cup": "volumen",
    "dash": "volumen",
    "pinch": "volumen",
}

# =========================================================
# VALIDACIÓN MATEMÁTICA
# =========================================================

def conversion_valida(origen: str, destino: str) -> bool:
    """
    ✔ Verifica si se pueden convertir dos unidades

    MATEMÁTICA APLICADA:
    - Solo se permiten conversiones dentro del mismo tipo:
      masa ↔ masa
      volumen ↔ volumen
    """
    return (
        origen in FACTORES
        and destino in FACTORES
        and TIPO_UNIDAD[origen] == TIPO_UNIDAD[destino]
    )


# =========================================================
# CONVERSIÓN DE UNIDADES (CAMBIO DE ESCALA)
# =========================================================

def convertir(cantidad: float, origen: str, destino: str) -> float:
    """
    🔢 AQUÍ ESTÁ LA CONVERSIÓN MATEMÁTICA

    Se usa un sistema de 2 pasos:

    1) Convertir a unidad base:
        base = cantidad × factor_origen

    2) Convertir a unidad final:
        resultado = base ÷ factor_destino

    Esto es un cambio de escala (proporciones).
    """

    base = cantidad * FACTORES[origen]
    return base / FACTORES[destino]


# =========================================================
# ENDPOINT PRINCIPAL
# =========================================================

@app.post("/ajustar-receta")
def ajustar_receta(data: RecetaRequest):

    # =====================================================
    # VALIDACIÓN (evita división por cero)
    # =====================================================
    if data.invitados_originales <= 0 or data.invitados_nuevos <= 0:
        raise HTTPException(status_code=400, detail="Cantidad de invitados inválida")

    # =====================================================
    # 🔢 MATEMÁTICA PRINCIPAL: REGLA DE TRES
    # =====================================================
    """
    Regla de tres directa:

        invitados_originales → cantidad original
        invitados_nuevos     → cantidad ajustada

    factor = nuevos / originales

    Ejemplo:
        2 personas → 100g harina
        4 personas → ?

        factor = 4 / 2 = 2
        nueva cantidad = 100 × 2 = 200g
    """

    factor = data.invitados_nuevos / data.invitados_originales

    ingredientes_ajustados = []

    for ing in data.ingredientes:

        # =================================================
        # VALIDACIÓN DE UNIDADES
        # =================================================
        if ing.unidadEntrada not in FACTORES or ing.unidadSalida not in FACTORES:
            raise HTTPException(
                status_code=400,
                detail=f"Unidad no soportada: {ing.unidadEntrada} o {ing.unidadSalida}"
            )

        # =================================================
        # VALIDACIÓN MATEMÁTICA DE COMPATIBILIDAD
        # =================================================
        if not conversion_valida(ing.unidadEntrada, ing.unidadSalida):
            raise HTTPException(
                status_code=400,
                detail=f"No se puede convertir de {ing.unidadEntrada} a {ing.unidadSalida}"
            )

        # =================================================
        # 🔢 APLICACIÓN DE REGLA DE TRES
        # =================================================
        cantidad_ajustada = ing.cantidad * factor

        # =================================================
        # 🔢 CONVERSIÓN DE UNIDADES (PROPORCIONES)
        # =================================================
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

    # =====================================================
    # RESPUESTA FINAL
    # =====================================================
    return {
        "factor": round(factor, 6),
        "ingredientes": ingredientes_ajustados
    }
