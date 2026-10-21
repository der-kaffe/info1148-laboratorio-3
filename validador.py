"""Validador léxico y sintáctico de la GLC del Laboratorio 3 (sin semántica)."""
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

    def analizar(self, fragment):
        if fragment:
            arbol = self._instruccion()
        else:
            begin = self._tomar("BEGIN", "«Begin» (distingue mayúsculas y minúsculas)")
            programa = self._tomar("PROGRAMA", "«Programa» después de «Begin»")
            nombre = self._tomar("ID", "el identificador del programa")
            instrucciones = []
            while self.actual["token"] not in {"END", "EOF"}:
                instrucciones.append(self._instruccion())
            if not instrucciones:
                self._error("al menos una instrucción")
            # Construye exactamente la producción recursiva por la derecha.
            lista = _nodo("lista_instrucciones", instrucciones[-1])
            for instruccion in reversed(instrucciones[:-1]):
                lista = _nodo("lista_instrucciones", instruccion, lista)
            end = self._tomar("END", "«End» para cerrar el programa")
            arbol = _nodo("programa", begin, programa, nombre, lista, end)
        if self.actual["token"] != "EOF":
            self._error("el fin de la entrada")
        return arbol


def validate(source: str, fragment=False, extension=False) -> dict:
    """Valida un programa o una instrucción; no evalúa valores, tipos ni nombres."""
    if not isinstance(source, str):
        raise TypeError("source debe ser una cadena de texto")
    resultado = {"valido": False, "modo": "instruccion" if fragment else "programa",
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", nargs="?", help="archivo UTF-8; sin archivo se lee la entrada estándar")
    parser.add_argument("--cadena", help="texto que se valida en lugar de un archivo")
    parser.add_argument("--fragmento", action="store_true", help="validar una sola instrucción")
    parser.add_argument("--extension", action="store_true", help="admitir declaraciones entero/real")
    parser.add_argument("--json", action="store_true", dest="salida_json", help="mostrar el resultado completo en JSON")
    args = parser.parse_args(argv)
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
        print(f"Válido: {resultado['modo']}" + (" con extensión C." if args.extension else "."))
    else:
        error = resultado["error"]
        print(f"Inválido ({error['fase']}, línea {error['linea']}, columna {error['columna']}): {error['mensaje']}")
    return 0 if resultado["valido"] else 1


if __name__ == "__main__":
    sys.exit(main())
