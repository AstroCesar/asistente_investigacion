"""Muestra los datos objetivos para revisar la ficha del Bloque 34."""

import sys

from ficha_datos import RUTA, cargar


def lista(elementos):
    return ", ".join(elementos) if elementos else "ninguno"


def resumen(ficha):
    rf, rnf, cajones = ficha["rf"], ficha["rnf"], ficha["cajones"]
    con_criterio = {rid for criterio in ficha["criterios"] for rid in criterio["cubre"]}
    probados = {cid for hito in ficha["hitos"] for cid in hito["criterios"]}
    ids_criterios = {criterio["id"] for criterio in ficha["criterios"]}
    exigidos = cajones["Imprescindible"] + list(rnf)

    print(f"RF: {len(rf)} | RNF: {len(rnf)}")
    print(
        f"Alcance: imprescindibles {len(cajones['Imprescindible'])}, "
        f"deseables {len(cajones['Deseable'])}, "
        f"fuera de alcance {len(cajones['Fuera de alcance'])}"
    )
    print(f"Criterios de aceptacion: {len(ficha['criterios'])}")
    print(
        "Imprescindibles y RNF sin criterio:",
        lista([rid for rid in exigidos if rid not in con_criterio]),
    )

    total = sum(hito["horas"] for hito in ficha["hitos"])
    disponibles, margen = ficha["disponibles"], ficha["margen"]
    linea = f"Hitos: {len(ficha['hitos'])} | Horas planificadas: {total:.1f} h"
    if disponibles is not None and margen is not None:
        tope = disponibles - margen
        linea += f" de {tope:.1f} h posibles"
        linea += f" ({disponibles:.1f} h menos {margen:.1f} h de margen)"
    print(linea)
    print(
        "Criterios que ningun hito comprueba:",
        lista(sorted(ids_criterios - probados)),
    )
    print(
        "Hitos sin criterio:",
        lista([hito["id"] for hito in ficha["hitos"] if not hito["criterios"]]),
    )


if __name__ == "__main__":
    if not RUTA.exists():
        sys.exit(f"No existe {RUTA}. Ejecuta el script desde la raiz.")
    resumen(cargar())
