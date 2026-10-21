"""Deriva por la izquierda a partir del árbol del validador, con las producciones de gramatica.bnf.

Las formas sentenciales usan los terminales de categoría ``ID`` y ``NUM`` tal como aparecen en la
gramática. El último paso es la sustitución léxica: cada ``ID``/``NUM`` se reemplaza por su lexema
(``z``, ``x``, ``20``…). Ese paso no es una producción de P; la elección del lexema es léxica.

``desde="programa"`` parte del símbolo inicial <programa> (derivación completa desde S).
``desde="instruccion"`` parte de <instruccion> y deriva solo la instrucción, es decir,
demuestra que la cadena pertenece a L(<instruccion>).
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validador import validate

CATEGORIAS = ("ID", "NUM")


def _texto(nodo, lexemas=False):
    if "simbolo" in nodo:
        return f"<{nodo['simbolo']}>"
    if nodo["token"] in CATEGORIAS and not lexemas:
        return nodo["token"]
    return nodo["lexema"]


def _forma(forma, lexemas=False):
    return " ".join(_texto(n, lexemas) for n in forma)


def derivacion_izquierda(raiz):
    """Formas sentenciales desde ``raiz``, expandiendo siempre el no terminal más a la izquierda.

    Si la forma final contiene ID o NUM, se agrega un último paso con los lexemas concretos.
    """
    forma = [raiz]
    pasos = [_forma(forma)]
    while True:
        posicion = next((i for i, n in enumerate(forma) if "simbolo" in n), None)
        if posicion is None:
            break
        forma = forma[:posicion] + forma[posicion]["hijos"] + forma[posicion + 1:]
        pasos.append(_forma(forma))
    lexica = _forma(forma, lexemas=True)
    if lexica != pasos[-1]:
        pasos.append(lexica)
    return pasos


def _instruccion(arbol):
    """Subárbol <instruccion> de un programa que contiene una sola instrucción."""
    return arbol["hijos"][3]["hijos"][0]


def derivar_texto(texto, fragmento=False, extension=False, desde="programa"):
    resultado = validate(texto, fragment=fragmento, extension=extension)
    if not resultado["valido"]:
        raise ValueError(resultado["error"]["mensaje"])
    if desde == "instruccion":
        if not fragmento:
            raise ValueError("desde='instruccion' requiere fragmento=True (una sola instrucción).")
        return derivacion_izquierda(_instruccion(resultado["arbol"]))
    return derivacion_izquierda(resultado["arbol"])


def formatear(pasos):
    return "\n".join(p if i == 0 else "⇒ " + p for i, p in enumerate(pasos))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cadena", required=True)
    ap.add_argument("--fragmento", action="store_true", help="la cadena es una sola instrucción")
    ap.add_argument("--extension", action="store_true")
    ap.add_argument("--desde", choices=("programa", "instruccion"), default="programa",
                    help="símbolo desde el que se deriva (instruccion requiere --fragmento)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    print(formatear(derivar_texto(a.cadena, a.fragmento, a.extension, a.desde)))
