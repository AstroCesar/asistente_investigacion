"""Comprueba la ficha y el registro de revisión del Bloque 34."""

import re
import sys
from pathlib import Path

from ficha_datos import RUTA, cargar
from verificar_ficha import verificar


REVISION = Path("docs/revision_alcance.md")
MIN_HITOS, MAX_HITOS = 3, 6


def verificar_pendientes(ficha):
    errores = []
    for numero in (4, 5):
        texto = ficha[f"texto{numero}"]
        if "[PENDIENTE" in texto or "[COMPLETAR" in texto:
            errores.append(f"la seccion {numero} todavia tiene marcas")
    return errores


def verificar_criterios(ficha):
    errores, avisos = [], []
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    if not ficha["criterios"]:
        errores.append("la seccion 4 no tiene criterios (formato CA-NN)")
    escritos = len(re.findall(r"(?m)^- CA", ficha["texto4"]))
    if escritos != len(ficha["criterios"]):
        errores.append(
            f"{escritos - len(ficha['criterios'])} criterio(s) "
            "no siguen el formato '- CA-NN (RF-NN): texto'"
        )
    cubiertos = set()
    for criterio in ficha["criterios"]:
        if not criterio["cubre"]:
            errores.append(f"{criterio['id']} no indica que RF o RNF cubre")
        for rid in criterio["cubre"]:
            if rid not in existentes:
                errores.append(f"{criterio['id']} cubre {rid}, que no existe")
        cubiertos.update(criterio["cubre"])
        if not re.search(r'\d|"', criterio["texto"]):
            avisos.append(f"{criterio['id']} no tiene ningun dato concreto")
    exigidos = ficha["cajones"]["Imprescindible"] + list(ficha["rnf"])
    for rid in exigidos:
        if rid not in cubiertos:
            errores.append(f"{rid} no tiene criterio de aceptacion")
    return errores, avisos


def verificar_plan(ficha):
    errores = []
    hitos = ficha["hitos"]
    ids_ca = {criterio["id"] for criterio in ficha["criterios"]}
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    escritos = len(re.findall(r"(?m)^- H\d", ficha["texto5"]))
    if escritos != len(hitos):
        errores.append(
            f"{escritos - len(hitos)} hito(s) no siguen el formato "
            "'- H1 (3 h): descripcion. Cubre: ... Se comprueba con: ...'"
        )
    if not MIN_HITOS <= len(hitos) <= MAX_HITOS:
        errores.append(f"hay {len(hitos)} hitos y se piden entre {MIN_HITOS} y {MAX_HITOS}")
    if ficha["disponibles"] is None or ficha["margen"] is None:
        errores.append("faltan las lineas 'Horas disponibles:' y 'Margen de imprevistos:'")
    else:
        tope = ficha["disponibles"] - ficha["margen"]
        total = sum(hito["horas"] for hito in hitos)
        if total > tope:
            errores.append(f"los hitos suman {total:.1f} h y el tope es {tope:.1f} h")
    cubiertos, probados = set(), set()
    for hito in hitos:
        if not hito["cubre"]:
            errores.append(f"{hito['id']} no indica que cubre")
        if not hito["criterios"]:
            errores.append(f"{hito['id']} no tiene criterio de aceptacion")
        for rid in hito["cubre"]:
            if rid not in existentes:
                errores.append(f"{hito['id']} cubre {rid}, que no existe")
        for cid in hito["criterios"]:
            if cid not in ids_ca:
                errores.append(f"{hito['id']} usa {cid}, que no existe")
        cubiertos.update(hito["cubre"])
        probados.update(hito["criterios"])
    for rid in ficha["cajones"]["Imprescindible"]:
        if rid not in cubiertos:
            errores.append(f"{rid} imprescindible sin hito que lo cubra")
    for cid in sorted(ids_ca - probados):
        errores.append(f"{cid} no lo comprueba ningun hito")
    return errores


def verificar_revision(ruta=REVISION):
    if not ruta.exists():
        return [f"falta {ruta.as_posix()}: registra la revision cruzada"]
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    patron_hallazgo = re.compile(r"^- Hallazgo \d+(?: \([^)]*\))?: .+$")
    patron_decision = re.compile(r"^  Decisión: (?:aceptado|rechazado|aplazado)\b.+$")
    indices = [i for i, linea in enumerate(lineas) if patron_hallazgo.match(linea)]
    errores = []
    if len(indices) < 2:
        errores.append(f"hay {len(indices)} hallazgos y se piden 2")
    if any(i + 1 >= len(lineas) or not patron_decision.match(lineas[i + 1]) for i in indices):
        errores.append("cada hallazgo necesita su linea 'Decisión:'")
    return errores


def ejecutar():
    if not RUTA.exists():
        sys.exit(f"No existe {RUTA}. Ejecuta el script desde la raiz.")
    errores, avisos = verificar(RUTA.read_text(encoding="utf-8"))
    if not errores:
        ficha = cargar()
        errores = verificar_pendientes(ficha)
        if not errores:
            errores, avisos_ca = verificar_criterios(ficha)
            errores += verificar_plan(ficha)
            avisos += avisos_ca
        if not errores:
            errores = verificar_revision()
    for aviso in avisos:
        print("AVISO:", aviso)
    for error in errores:
        print("ERROR:", error)
    if errores:
        print(f"\n{len(errores)} problema(s) por resolver")
        return 1
    print("Ficha verificada: las cinco secciones son coherentes")
    return 0


if __name__ == "__main__":
    sys.exit(ejecutar())
