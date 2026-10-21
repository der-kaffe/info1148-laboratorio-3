"""Pruebas del lenguaje, su árbol de derivación y la interfaz de ejecución."""
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
# El proceso hijo debe hablar UTF-8 aunque la consola de Windows use cp1252.
ENTORNO_UTF8 = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
sys.path.insert(0, str(ROOT))
from validador import LETRAS, validate
from herramientas.derivacion import derivar_texto


def nodos(arbol):
    if "simbolo" in arbol:
        yield arbol["simbolo"]
        for hijo in arbol["hijos"]:
            yield from nodos(hijo)


def hojas(arbol):
    """Hojas reales del árbol; se omiten los tokens virtuales del programa mínimo de un fragmento."""
    if "token" in arbol:
        if not arbol.get("virtual"):
            yield arbol
    else:
        for hijo in arbol["hijos"]:
            yield from hojas(hijo)


class LenguajeTests(unittest.TestCase):
    def assertValido(self, texto, **opciones):
        resultado = validate(texto, **opciones)
        self.assertTrue(resultado["valido"], resultado["error"])
        self.assertIsNone(resultado["error"])
        self.assertEqual(list(hojas(resultado["arbol"])), resultado["tokens"])
        return resultado

    def assertInvalido(self, texto, fase="sintáctico", **opciones):
        resultado = validate(texto, **opciones)
        self.assertFalse(resultado["valido"])
        self.assertIsNone(resultado["arbol"])
        self.assertEqual(resultado["error"]["fase"], fase)
        self.assertTrue(resultado["error"]["mensaje"])
        self.assertGreaterEqual(resultado["error"]["linea"], 1)
        self.assertGreaterEqual(resultado["error"]["columna"], 1)
        return resultado

    def test_casos_del_enunciado_y_sus_dos_lecturas_de_barras(self):
        casos = json.loads((ROOT / "ejemplos/casos_validacion.json").read_text(encoding="utf-8"))
        for caso in casos:
            with self.subTest(caso=caso["id"]):
                resultado = validate(caso["texto"], fragment=caso["fragmento"], extension=caso["extension"])
                self.assertEqual(resultado["valido"], caso["esperado"], resultado["error"])

    def test_tres_cadenas_de_la_pregunta_3(self):
        for texto in ("x = 20 #", "z = x * y #", "salida temporal #"):
            with self.subTest(texto=texto):
                self.assertValido(texto, fragment=True)

    def test_programa_referencia_completo_de_20_instrucciones(self):
        texto = (ROOT / "ejemplos/programa_referencia.txt").read_text(encoding="utf-8")
        resultado = self.assertValido(texto)
        cuentas = Counter(nodos(resultado["arbol"]))
        self.assertEqual(cuentas["instruccion"], 20)
        self.assertEqual(cuentas["lista_instrucciones"], 20)
        self.assertEqual(cuentas["asignacion_simple"], 6)
        self.assertEqual(cuentas["asignacion_aritmetica"], 7)
        self.assertEqual(cuentas["salida"], 7)
        lista = resultado["arbol"]["hijos"][3]
        for _ in range(19):
            self.assertEqual(lista["simbolo"], "lista_instrucciones")
            self.assertEqual(len(lista["hijos"]), 2)
            self.assertEqual(lista["hijos"][0]["simbolo"], "instruccion")
            lista = lista["hijos"][1]
        self.assertEqual(lista["simbolo"], "lista_instrucciones")
        self.assertEqual(len(lista["hijos"]), 1)

    def test_arbol_aritmetico_respeta_todas_las_producciones(self):
        resultado = self.assertValido("z = x + y #", fragment=True)
        t = resultado["tokens"]
        instruccion = resultado["arbol"]["hijos"][3]["hijos"][0]
        esperado = {"simbolo": "instruccion", "hijos": [
            {"simbolo": "asignacion_aritmetica", "hijos": [t[0], t[1],
                {"simbolo": "expresion", "hijos": [
                    {"simbolo": "operando", "hijos": [t[2]]},
                    {"simbolo": "operador", "hijos": [t[3]]},
                    {"simbolo": "operando", "hijos": [t[4]]}]}, t[5]]}]}
        self.assertEqual(instruccion, esperado)
        self.assertEqual(resultado["arbol"]["simbolo"], "programa")
        self.assertEqual(t[3]["token"], "OPERADOR")
        self.assertEqual(t[3]["lexema"], "+")

    def test_asignacion_simple_no_agrega_nodo_expresion(self):
        resultado = self.assertValido("x=0#", fragment=True)
        cuentas = Counter(nodos(resultado["arbol"]))
        self.assertEqual(cuentas["asignacion_simple"], 1)
        self.assertEqual(cuentas["operando"], 1)
        self.assertNotIn("expresion", cuentas)

    def test_cinco_operadores_y_exactamente_una_operacion(self):
        for operador in "+-*/%":
            with self.subTest(operador=operador):
                resultado = self.assertValido(f"x = 3 {operador} 2 #", fragment=True)
                self.assertIn(operador, [t["lexema"] for t in resultado["tokens"]])
        for texto in ("x=1+2+3#", "x=a+b*c#", "x=1++2#", "x=1 2#"):
            with self.subTest(texto=texto):
                self.assertInvalido(texto, fragment=True)

    def test_modo_programa_y_fragmento(self):
        # L(G) solo contiene programas: una instrucción suelta no es un programa.
        self.assertInvalido("x=1#")
        # Un fragmento es válido si es exactamente una instrucción: pertenece a L(<instruccion>).
        self.assertValido("x=1#", fragment=True)
        self.assertInvalido("x=1# salida x#", fragment=True)
        programa = "Begin Programa p x=1# End"
        self.assertValido(programa)
        self.assertInvalido(programa, fragment=True)
        for texto in ("", "Begin Programa p End", "Begin Programa p x=1#", programa + " x=2#"):
            with self.subTest(texto=texto):
                self.assertInvalido(texto)
        self.assertInvalido("", fragment=True)

    def test_fragmento_equivale_a_programa_minimo(self):
        cadenas = ["x = 10 #", "z = x + y #", "salida z #", "x 10 #", "z = + x y #", "salida #", "x = 20",
                   "", "x=1+2+3#", "x=1# End", "Begin Programa q x=1# End", "x=#", "= 1 #"]
        for cadena in cadenas:
            with self.subTest(cadena=cadena):
                como_fragmento = validate(cadena, fragment=True)["valido"]
                como_programa = validate("Begin Programa prueba\n" + cadena + "\nEnd")["valido"]
                self.assertEqual(como_fragmento, como_programa)

    def test_instruccion_suelta_pertenece_a_instruccion_pero_no_a_programa(self):
        for texto in ("x = 20 #", "z = x * y #", "salida temporal #", "z = x + y #"):
            with self.subTest(texto=texto):
                self.assertValido(texto, fragment=True)
                self.assertInvalido(texto)
        # Dos instrucciones ya no son una instrucción, aunque sí forman un programa válido.
        self.assertInvalido("x = 1 # y = 2 #", fragment=True)
        self.assertValido("Begin Programa p x = 1 # y = 2 # End")

    def test_arbol_siempre_tiene_raiz_programa(self):
        for texto, opciones in (("x=1#", {"fragment": True}), ("Begin Programa p x=1# End", {})):
            arbol = self.assertValido(texto, **opciones)["arbol"]
            self.assertEqual(arbol["simbolo"], "programa")
            self.assertEqual([h.get("simbolo") or h["token"] for h in arbol["hijos"]],
                             ["BEGIN", "PROGRAMA", "ID", "lista_instrucciones", "END"])

    def test_extension_c_y_reservadas_solo_cuando_esta_activa(self):
        for tipo in ("entero", "real"):
            self.assertValido(f"{tipo} dato #", fragment=True, extension=True)
            self.assertInvalido(f"{tipo} dato #", fragment=True)
            self.assertValido(f"{tipo}=1#", fragment=True)
            self.assertInvalido(f"{tipo}=1#", fragment=True, extension=True)
        texto = (ROOT / "ejemplos/programa_extendido.txt").read_text(encoding="utf-8")
        resultado = self.assertValido(texto, extension=True)
        self.assertEqual(Counter(nodos(resultado["arbol"]))["declaracion"], 2)
        self.assertInvalido(texto)
        self.assertInvalido("entero #", fragment=True, extension=True)

    def test_mayusculas_y_maxima_longitud_de_reservadas(self):
        for nombre in ("salida2", "Beginner", "Programa_1", "End2", "Entero", "realidad"):
            self.assertValido(f"{nombre}=1#", fragment=True, extension=True)
        self.assertInvalido("begin Programa p x=1# End")
        self.assertInvalido("Begin programa p x=1# End")
        self.assertInvalido("Begin Programa p x=1# end")
        self.assertInvalido("salida = 1#", fragment=True)

    def test_alfabeto_exacto_de_identificadores(self):
        self.assertEqual(len(LETRAS), 66)
        for letra in LETRAS:
            self.assertValido(f"{letra}_2=0#", fragment=True)
        for texto in ("_dato=1#", "å=1#", "Ж=1#", "x=١#"):
            with self.subTest(texto=texto):
                self.assertInvalido(texto, fase="léxico", fragment=True)

    def test_numeros_sin_signo_sin_exponente_y_con_cero(self):
        for numero in ("0", "007", "1.345", "12.0"):
            self.assertValido(f"x={numero}#", fragment=True)
        for numero in ("-1", "+1", "1e3"):
            self.assertInvalido(f"x={numero}#", fragment=True)
        for numero in (".5", "1.", "1.2.3"):
            self.assertInvalido(f"x={numero}#", fase="léxico", fragment=True)

    def test_no_hay_cadenas_ni_parentesis(self):
        for texto in ('x="hola"#', "x=(1+2)#", "x=@#"):
            self.assertInvalido(texto, fase="léxico", fragment=True)

    def test_comentarios_y_posiciones(self):
        resultado = self.assertValido("/* uno\n dos */\nÁrbol_2 = 0 #", fragment=True)
        self.assertEqual([(t["linea"], t["columna"]) for t in resultado["tokens"]],
                         [(3, 1), (3, 9), (3, 11), (3, 13)])
        self.assertEqual(resultado["tokens"][0]["lexema"], "Árbol_2")
        self.assertValido("x=1/* comentario */+2#", fragment=True)
        self.assertValido("x=1/* exterior /* interior */+2#", fragment=True)
        self.assertInvalido("Be/* comentario */gin Programa p x=1# End")
        error = self.assertInvalido("Begin\n/* sin cierre", fase="léxico")["error"]
        self.assertEqual((error["linea"], error["columna"]), (2, 1))

    def test_crlf_y_cr_cuentan_lineas_sin_normalizar_la_entrada(self):
        for salto in ("\n", "\r\n", "\r"):
            texto = salto.join(("Begin", "Programa p", "x=0#", "End"))
            resultado = self.assertValido(texto)
            self.assertEqual((resultado["tokens"][-1]["linea"], resultado["tokens"][-1]["columna"]), (4, 1))

    def test_barras_literales_no_son_saltos_ni_comentarios_de_linea(self):
        texto = "Begin / Programa p / x=1# / End"
        resultado = self.assertInvalido(texto)
        self.assertEqual(sum(t["lexema"] == "/" for t in resultado["tokens"]), 3)
        resultado = self.assertInvalido("x=1//2#", fragment=True)
        self.assertEqual(sum(t["lexema"] == "/" for t in resultado["tokens"]), 2)
        self.assertValido("x=1/2#", fragment=True)

    def test_no_se_evalua_semantica(self):
        self.assertValido("Begin Programa p salida desconocido# x=1/0# x=y# End")
        self.assertValido("Begin Programa p entero x# x=1.5# End", extension=True)

    def test_contrato_json_y_error_en_fin_de_entrada(self):
        resultado = self.assertInvalido("x = 20", fragment=True)
        self.assertEqual(set(resultado), {"valido", "modo", "lenguaje", "extension", "tokens", "arbol", "error"})
        self.assertEqual(resultado["modo"], "fragmento")
        self.assertEqual(resultado["lenguaje"], "L(<instruccion>)")
        self.assertEqual((resultado["error"]["linea"], resultado["error"]["columna"]), (1, 7))
        for token in resultado["tokens"]:
            self.assertEqual(set(token), {"token", "lexema", "linea", "columna"})
            self.assertNotEqual(token["token"], "EOF")
        self.assertEqual(json.loads(json.dumps(resultado, ensure_ascii=False)), resultado)


class CLITests(unittest.TestCase):
    def ejecutar(self, *args, entrada=None):
        return subprocess.run([sys.executable, str(ROOT / "validador.py"), *args],
                              input=entrada, text=True, encoding="utf-8", capture_output=True,
                              env=ENTORNO_UTF8)

    def test_cadena_json_y_error_de_sintaxis(self):
        valido = self.ejecutar("--fragmento", "--cadena", "salida z#", "--json")
        self.assertEqual(valido.returncode, 0, valido.stderr)
        self.assertTrue(json.loads(valido.stdout)["valido"])
        invalido = self.ejecutar("--fragmento", "--cadena", "salida #", "--json")
        self.assertEqual(invalido.returncode, 1)
        self.assertEqual(json.loads(invalido.stdout)["error"]["fase"], "sintáctico")

    def test_stdin_y_archivo(self):
        resultado = self.ejecutar("--fragmento", entrada="x=0#")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("Válido", resultado.stdout)
        resultado = self.ejecutar(str(ROOT / "ejemplos/programa_referencia.txt"), "--json")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(json.loads(resultado.stdout)["modo"], "programa")
        self.assertEqual(json.loads(resultado.stdout)["lenguaje"], "L(<programa>)")

    def test_derivacion_izquierda_desde_el_simbolo_inicial(self):
        pasos = derivar_texto("z = x + y #", fragmento=True)
        self.assertEqual(pasos[0], "<programa>")
        # Las formas sentenciales usan la categoría ID; el último paso es la sustitución léxica.
        self.assertEqual(pasos[-2], "Begin Programa ID ID = ID + ID # End")
        self.assertEqual(pasos[-1], "Begin Programa prueba z = x + y # End")
        self.assertEqual(len(pasos), 10)
        pasos = derivar_texto("salida z #", fragmento=True)
        self.assertEqual(pasos[-1], "Begin Programa prueba salida z # End")
        self.assertEqual(len(pasos), 6)

    def test_derivacion_izquierda_desde_instruccion(self):
        pasos = derivar_texto("z = x + y #", fragmento=True, desde="instruccion")
        self.assertEqual(pasos, ["<instruccion>", "<asignacion_aritmetica>", "ID = <expresion> #",
                                 "ID = <operando> <operador> <operando> #", "ID = ID <operador> <operando> #",
                                 "ID = ID + <operando> #", "ID = ID + ID #", "z = x + y #"])
        self.assertEqual(derivar_texto("salida z #", fragmento=True, desde="instruccion"),
                         ["<instruccion>", "<salida>", "salida ID #", "salida z #"])
        self.assertEqual(derivar_texto("entero edad #", fragmento=True, extension=True, desde="instruccion"),
                         ["<instruccion>", "<declaracion>", "<tipo> ID #", "entero ID #", "entero edad #"])

    def test_errores_de_uso_y_lectura(self):
        resultado = self.ejecutar(str(ROOT / "ejemplos/programa_referencia.txt"), "--cadena", "x=1#")
        self.assertEqual(resultado.returncode, 2)
        resultado = self.ejecutar(str(ROOT / "ejemplos/archivo_inexistente_para_prueba.txt"))
        self.assertEqual(resultado.returncode, 2)
        self.assertIn("No se pudo leer", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
