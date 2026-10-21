# Laboratorio 3: Diseño y Validación de Gramáticas

Solución propuesta para el Laboratorio 3 de Teoría de la Computación (INFO1148). Incluye informe, gramática, derivaciones, árbol sintáctico y evidencias reproducibles.

## Leer el informe

- [Informe en HTML](docs/Informe_Laboratorio_3.html)
- [Informe en PDF](docs/Informe_Laboratorio_3.pdf)
- [Enunciado original](docs/Laboratorio_3_enunciado.pdf)
- [Gramática base y extensión](gramatica.bnf)
- [Árbol sintáctico](docs/arbol_z_x_mas_y.svg)
- [Resultados de validación](evidencias/validacion.json)

## Ejecutar el validador

El validador usa únicamente la biblioteca estándar de Python 3.

```bash
python3 validador.py ejemplos/programa_referencia.txt
python3 validador.py --fragmento --cadena "z = x + y #"
python3 validador.py ejemplos/programa_extendido.txt --extension
python3 validador.py --fragmento --cadena "salida #" --json
```

Salida de proceso: `0` si la cadena es válida, `1` si es inválida y `2` para un problema de uso o de lectura del archivo. El modo predeterminado exige un programa completo. `--fragmento` comprueba una sola instrucción.

## Comprobar las evidencias

```bash
python3 -m unittest discover -s pruebas -v
python3 herramientas/generar_evidencias.py
```

El segundo comando vuelve a crear `evidencias/validacion.json` con los casos del enunciado y ambos programas. No transforma el texto que se valida.

Para regenerar el informe y las figuras, se requieren Graphviz (`dot`), las fuentes DejaVu y las dependencias de `requirements-informe.txt`:

```bash
python3 -m pip install -r requirements-informe.txt
python3 herramientas/generar_informe.py
```

El generador busca las fuentes en `/usr/share/fonts/truetype/dejavu`, la ruta usada por esta entrega en Linux. La ejecución del validador y sus pruebas no requiere esas dependencias.

## Alcance de la propuesta

- Programa: `Begin Programa ID` seguido de una o más instrucciones y `End`.
- Asignación simple: `ID = operando #`.
- Asignación aritmética: `ID = operando operador operando #`, con exactamente una operación binaria. Los operadores son `+`, `-`, `*`, `/` y `%`.
- Salida: `salida ID #`.
- Extensión C: declaraciones `entero ID #` y `real ID #`, activadas con `--extension`.
- No se incluyen paréntesis, operaciones encadenadas, signos unarios ni comprobaciones de tipos, valores o declaración previa.

`ID` y `NUM` son categorías léxicas, no una lista de nombres o valores particulares. Los identificadores empiezan con una letra y continúan con letras, dígitos o `_`. Se admiten las letras castellanas indicadas en el informe. Los números son decimales sin signo, con dígitos obligatorios a ambos lados del punto cuando existe; se admite `0`, tal como hace el programa de referencia.

Las palabras reservadas distinguen mayúsculas y minúsculas. Los espacios y comentarios `/* ... */` se descartan en el análisis léxico. Los comentarios no se anidan. `//` no es un comentario en esta propuesta.

## Caso 8 del enunciado

El PDF muestra barras `/` entre las líneas del programa. En el informe se comprueban las dos lecturas:

1. Como separadores editoriales de líneas, el programa de `ejemplos/caso_8_programa.txt` es válido.
2. Como caracteres literales, la cadena `caso_8_literal` de `ejemplos/casos_validacion.json` es inválida.

El validador nunca sustituye `/` por saltos de línea. La división sigue siendo un operador y `/* ... */` sigue siendo un comentario.

## Estructura

```text
gramatica.bnf                Producciones base y extensión C
validador.py                 Analizador léxico y sintáctico
ejemplos/                    Programa original, extensión y casos de prueba
pruebas/                     Pruebas automatizadas independientes
evidencias/                  Resultados reproducibles y árbol de la instrucción
docs/                       Informe, enunciado y figuras
herramientas/               Generación de evidencias e informe
```

El árbol se dibuja con Graphviz y se entrega también en DOT, SVG y PNG. No se utilizó JFLAP.

El enunciado docente conserva su autoría y sus condiciones de uso. No se otorga una licencia abierta sobre ese PDF.
