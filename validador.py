"""Validador léxico y sintáctico de la GLC del Laboratorio 3 (sin semántica).

Dos juicios de pertenencia, que el informe distingue explícitamente:

* Modo programa (por defecto): ¿la entrada pertenece a L(<programa>)? Con S = <programa>,
  este es el lenguaje generado por la gramática: programas completos ``Begin Programa … End``.
* Modo ``--fragmento``: ¿la entrada es exactamente una instrucción, es decir, pertenece a
  L(<instruccion>)? Para una instrucción w se cumple: w ∈ L(<instruccion>) si y solo si
  ``Begin Programa prueba w End`` ∈ L(<programa>). Por eso el árbol devuelto siempre tiene
  raíz <programa>, y los tokens del programa mínimo se marcan como virtuales.

Una instrucción suelta pertenece a L(<instruccion>) pero no a L(<programa>).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


LETRAS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÑñÁÉÍÓÚÜáéíóúü")
DIGITOS = frozenset("0123456789")
OPERADORES = frozenset("+-*/%")
RESERVADAS = {"Begin": "BEGIN", "Programa": "PROGRAMA", "End": "END", "salida": "SALIDA"}


class _ErrorValidacion(Exception):
    def __init__(self, fase, mensaje, linea, columna):
        super().__init__(mensaje)
        self.datos = {"fase": fase, "mensaje": mensaje, "linea": linea, "columna": columna}


class _Lexer:
    def __init__(self, source, extension):
        self.source = source
        self.i = 0
        self.linea = 1
        self.columna = 1
        self.tokens = []
        self.reservadas = dict(RESERVADAS)
        if extension:
            self.reservadas.update({"entero": "ENTERO", "real": "REAL"})

    def _avanzar(self):
        """Cuenta posiciones desde 1; CRLF se considera un único salto."""
        char = self.source[self.i]
        self.i += 1
        if char == "\r":
            if self.i < len(self.source) and self.source[self.i] == "\n":
                self.i += 1
            self.linea += 1
            self.columna = 1
        elif char == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1

    def _token(self, tipo, inicio, linea, columna):
        self.tokens.append({"token": tipo, "lexema": self.source[inicio:self.i],
                            "linea": linea, "columna": columna})

    def analizar(self):
        while self.i < len(self.source):
            char = self.source[self.i]
            if char.isspace():
                self._avanzar()
                continue
            inicio, linea, columna = self.i, self.linea, self.columna
            if self.source.startswith("/*", self.i):
                self._avanzar()
                self._avanzar()
                while self.i < len(self.source) and not self.source.startswith("*/", self.i):
                    self._avanzar()
                if self.i == len(self.source):
                    raise _ErrorValidacion("léxico", "Comentario /* sin cierre */.", linea, columna)
                self._avanzar()
                self._avanzar()
                continue
            if char in LETRAS:
                self._avanzar()
                while self.i < len(self.source) and self.source[self.i] in LETRAS | DIGITOS | {"_"}:
                    self._avanzar()
                lexema = self.source[inicio:self.i]
                self._token(self.reservadas.get(lexema, "ID"), inicio, linea, columna)
            elif char in DIGITOS:
                while self.i < len(self.source) and self.source[self.i] in DIGITOS:
                    self._avanzar()
                if self.i < len(self.source) and self.source[self.i] == ".":
                    if self.i + 1 == len(self.source) or self.source[self.i + 1] not in DIGITOS:
                        raise _ErrorValidacion("léxico", "El decimal requiere dígitos después del punto.",
                                               self.linea, self.columna)
                    self._avanzar()
                    while self.i < len(self.source) and self.source[self.i] in DIGITOS:
                        self._avanzar()
                self._token("NUM", inicio, linea, columna)
            elif char in OPERADORES or char in "=#":
                self._avanzar()
                tipo = "IGUAL" if char == "=" else "FIN" if char == "#" else "OPERADOR"
                self._token(tipo, inicio, linea, columna)
            else:
                raise _ErrorValidacion("léxico", f"Carácter no admitido: «{char}».", linea, columna)
        return self.tokens


def _nodo(simbolo, *hijos):
    return {"simbolo": simbolo, "hijos": list(hijos)}


class _Parser:
    def __init__(self, tokens, linea_fin, columna_fin, extension):
        self.tokens = tokens
        self.fin = {"token": "EOF", "lexema": "", "linea": linea_fin, "columna": columna_fin}
        self.i = 0
        self.extension = extension

    @property
    def actual(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else self.fin

    def _error(self, esperado):
        token = self.actual
        encontrado = "el fin de la entrada" if token["token"] == "EOF" else f"«{token['lexema']}»"
        raise _ErrorValidacion("sintáctico", f"Se esperaba {esperado}; se encontró {encontrado}.",
                               token["linea"], token["columna"])

    def _tomar(self, tipo, esperado):
        if self.actual["token"] != tipo:
            self._error(esperado)
        token = self.actual
        self.i += 1
        return token

    def _operando(self):
        if self.actual["token"] not in {"ID", "NUM"}:
            self._error("un identificador o un número sin signo")
        token = self.actual
        self.i += 1
        return _nodo("operando", token)

    def _instruccion(self):
        if self.actual["token"] == "SALIDA":
            salida = self._tomar("SALIDA", "«salida»")
            identificador = self._tomar("ID", "un identificador después de «salida»")
            fin = self._tomar("FIN", "«#» para terminar la salida")
            return _nodo("instruccion", _nodo("salida", salida, identificador, fin))
        if self.extension and self.actual["token"] in {"ENTERO", "REAL"}:
            tipo = self.actual
            self.i += 1
            identificador = self._tomar("ID", "un identificador después del tipo")
            fin = self._tomar("FIN", "«#» para terminar la declaración")
            return _nodo("instruccion", _nodo("declaracion", _nodo("tipo", tipo), identificador, fin))
        if self.actual["token"] != "ID":
            opciones = "una asignación o «salida»"
            if self.extension:
                opciones += ", o una declaración «entero»/«real»"
            self._error(opciones)
        identificador = self._tomar("ID", "un identificador")
        igual = self._tomar("IGUAL", "«=» después del identificador")
        primero = self._operando()
        if self.actual["token"] == "OPERADOR":
            operador = self._tomar("OPERADOR", "un operador aritmético")
            segundo = self._operando()
            expresion = _nodo("expresion", primero, _nodo("operador", operador), segundo)
            fin = self._tomar("FIN", "«#» después de los dos operandos (solo se admite una operación)")
            asignacion = _nodo("asignacion_aritmetica", identificador, igual, expresion, fin)
        else:
            fin = self._tomar("FIN", "«#» para terminar la asignación, o un operador aritmético")
            asignacion = _nodo("asignacion_simple", identificador, igual, primero, fin)
        return _nodo("instruccion", asignacion)

    @staticmethod
    def _virtual(tipo, lexema):
        """Token implícito del programa mínimo que envuelve un fragmento (no está en la entrada)."""
        return {"token": tipo, "lexema": lexema, "linea": 0, "columna": 0, "virtual": True}

    def _instrucciones(self, hasta_end):
        instrucciones = []
        if not hasta_end:
            # Modo fragmento: exactamente una instrucción (L(<instruccion>)).
            if self.actual["token"] == "EOF":
                self._error("una instrucción")
            instrucciones.append(self._instruccion())
        while hasta_end and self.actual["token"] != "EOF" and self.actual["token"] != "END":
            instrucciones.append(self._instruccion())
        if not instrucciones:
            self._error("al menos una instrucción")
        # Construye exactamente la producción recursiva por la derecha:
        # <lista_instrucciones> ::= <instruccion> <lista_instrucciones> | <instruccion>
        lista = _nodo("lista_instrucciones", instrucciones[-1])
        for instruccion in reversed(instrucciones[:-1]):
            lista = _nodo("lista_instrucciones", instruccion, lista)
        return lista

    def analizar(self, fragment):
        """Siempre devuelve un árbol con raíz <programa>, el símbolo inicial de G."""
        if fragment:
            begin = self._virtual("BEGIN", "Begin")
            programa = self._virtual("PROGRAMA", "Programa")
            nombre = self._virtual("ID", "prueba")
            lista = self._instrucciones(hasta_end=False)
            end = self._virtual("END", "End")
        else:
            begin = self._tomar("BEGIN", "«Begin» (distingue mayúsculas y minúsculas)")
            programa = self._tomar("PROGRAMA", "«Programa» después de «Begin»")
            nombre = self._tomar("ID", "el identificador del programa")
            lista = self._instrucciones(hasta_end=True)
            end = self._tomar("END", "«End» para cerrar el programa")
        if self.actual["token"] != "EOF":
            self._error("el fin de la entrada")
        return _nodo("programa", begin, programa, nombre, lista, end)


def validate(source: str, fragment=False, extension=False) -> dict:
    """Valida un programa completo o, con ``fragment``, las instrucciones de un programa mínimo.

    No evalúa valores, tipos ni nombres. El árbol devuelto siempre tiene raíz <programa>.
    """
    if not isinstance(source, str):
        raise TypeError("source debe ser una cadena de texto")
    resultado = {"valido": False, "modo": "fragmento" if fragment else "programa",
                 "lenguaje": "L(<instruccion>)" if fragment else "L(<programa>)",
                 "extension": bool(extension), "tokens": [], "arbol": None, "error": None}
    lexer = _Lexer(source, extension)
    try:
        resultado["tokens"] = lexer.analizar()
        resultado["arbol"] = _Parser(lexer.tokens, lexer.linea, lexer.columna, extension).analizar(fragment)
        resultado["valido"] = True
    except _ErrorValidacion as error:
        resultado["tokens"] = lexer.tokens
        resultado["error"] = error.datos
    return resultado


def usar_utf8_en_flujos():
    """Fuerza UTF-8 en stdin/stdout/stderr (en Windows, con pipes, Python usa cp1252)."""
    for flujo in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", nargs="?", help="archivo UTF-8; sin archivo se lee la entrada estándar")
    parser.add_argument("--cadena", help="texto que se valida en lugar de un archivo")
    parser.add_argument("--fragmento", action="store_true", help="validar exactamente una instrucción (pertenencia a L(<instruccion>)) en lugar de un programa completo")
    parser.add_argument("--extension", action="store_true", help="admitir declaraciones entero/real")
    parser.add_argument("--json", action="store_true", dest="salida_json", help="mostrar el resultado completo en JSON")
    args = parser.parse_args(argv)
    usar_utf8_en_flujos()
    if args.archivo and args.cadena is not None:
        parser.error("archivo y --cadena son alternativas; use solo una")
    try:
        source = args.cadena if args.cadena is not None else (
            Path(args.archivo).read_text(encoding="utf-8") if args.archivo else sys.stdin.read())
    except (OSError, UnicodeError) as error:
        print(f"No se pudo leer la entrada: {error}", file=sys.stderr)
        return 2
    resultado = validate(source, fragment=args.fragmento, extension=args.extension)
    if args.salida_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    elif resultado["valido"]:
        print(f"Válido: {resultado['modo']}, pertenece a {resultado['lenguaje']}" + (" (con extensión C)." if args.extension else "."))
    else:
        error = resultado["error"]
        print(f"Inválido para {resultado['lenguaje']} ({error['fase']}, línea {error['linea']}, columna {error['columna']}): {error['mensaje']}")
    return 0 if resultado["valido"] else 1


if __name__ == "__main__":
    sys.exit(main())
