"""Genera los árboles de derivación (DOT, SVG y PNG) con Graphviz a partir del validador.

Se generan dos árboles de ``z = x + y #``:

* ``arbol_z_x_mas_y.*``           raíz <instruccion>: la cadena como elemento de L(<instruccion>).
* ``arbol_z_x_mas_y_programa.*``  raíz <programa> (símbolo inicial S): la misma instrucción dentro
                                  del programa mínimo ``Begin Programa prueba … End``.

Requiere el programa ``dot`` de Graphviz. Uso:
    python3 herramientas/generar_arbol.py [salida_dir]
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validador import validate

PROGRAMA = "Begin\nPrograma prueba\nz = x + y #\nEnd"
INSTRUCCION = "z = x + y #"


def _etiqueta(nodo):
    if "simbolo" in nodo:
        return f"<{nodo['simbolo']}>"
    return f"{nodo['token']}[{nodo['lexema']}]" if nodo["token"] in ("ID", "NUM") else nodo["lexema"]


def a_dot(arbol):
    lineas = ['digraph arbol {', '  graph [ordering=out, nodesep=0.25, ranksep=0.55, dpi=170];',
              '  node [fontname="Helvetica", fontsize=11, margin="0.10,0.05"];', '  edge [color="#555555"];']
    hojas, contador = [], [0]

    def visitar(nodo):
        nid = f"n{contador[0]}"
        contador[0] += 1
        etiqueta = _etiqueta(nodo).replace('"', '\\"')
        if "simbolo" in nodo:
            lineas.append(f'  {nid} [label="{etiqueta}", shape=box, style="rounded,filled", fillcolor="#dbe9f8", color="#2c5d94"];')
            for hijo in nodo["hijos"]:
                lineas.append(f"  {nid} -> {visitar(hijo)};")
        else:
            lineas.append(f'  {nid} [label="{etiqueta}", shape=box, style="filled", fillcolor="#dff3e0", color="#2e7d32"];')
            hojas.append(nid)
        return nid

    visitar(arbol)
    lineas.append("  { rank=same; " + "; ".join(hojas) + "; }")
    lineas.append("}")
    return "\n".join(lineas) + "\n"


def arbol_programa():
    """Árbol con raíz <programa> (símbolo inicial S)."""
    resultado = validate(PROGRAMA)
    assert resultado["valido"], resultado["error"]
    return resultado["arbol"]


def arbol_instruccion():
    """Árbol con raíz <instruccion>: z = x + y # ∈ L(<instruccion>)."""
    resultado = validate(INSTRUCCION, fragment=True)
    assert resultado["valido"], resultado["error"]
    return resultado["arbol"]["hijos"][3]["hijos"][0]


def _escribir(arbol, destino, nombre):
    dot = destino / f"{nombre}.dot"
    dot.write_text(a_dot(arbol), encoding="utf-8")
    for formato in ("svg", "png"):
        subprocess.run(["dot", f"-T{formato}", str(dot), "-o", str(destino / f"{nombre}.{formato}")], check=True)


def generar(destino):
    destino.mkdir(parents=True, exist_ok=True)
    _escribir(arbol_instruccion(), destino, "arbol_z_x_mas_y")
    _escribir(arbol_programa(), destino, "arbol_z_x_mas_y_programa")
    return destino


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "arbol_sintactico"))
