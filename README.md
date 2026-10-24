# Laboratorio 3: Diseño y Validación de Gramáticas

Teoría de la Computación · INFO1148

**Autores: Juan Cárdenas y Bayron Flores.**

## Informe y entrega

- [Informe PDF](docs/Informe_Laboratorio_3.pdf) (formato de la plantilla del laboratorio, secciones 1 a 5 y anexo)
- [Informe editable (.docx)](docs/Informe_Laboratorio_3.docx)
- [Gramática base, extensión y gramática léxica](gramatica.bnf)
- [Archivos JFLAP](jflap/): `lab3_base.jff` (17 producciones) y `lab3_extension.jff` (21 producciones), con [capturas](jflap/capturas/) de los árboles de `z = x + y #` y `salida z #` y de Multiple Brute Force Parse
- Árboles de derivación de `z = x + y #`: [desde `<instruccion>`](arbol_sintactico/arbol_z_x_mas_y.svg) y [desde `<programa>`](arbol_sintactico/arbol_z_x_mas_y_programa.svg) (también `.png` y `.dot`)
- [Derivaciones por la izquierda](evidencias/derivaciones.txt) y [resultados de validación](evidencias/validacion.json)
- [Entrega completa en Google Drive](https://drive.google.com/drive/folders/1SXU1cSjy1-m_Fg0xZlNUexpftVtnUft6?usp=sharing)

## Pertenencia: L(<programa>) y L(<instruccion>)

El símbolo inicial es `<programa>`, así que el lenguaje generado es L(G) = L(<programa>): **solo programas completos**
(`Begin Programa … End`). Una instrucción suelta, como `z = x + y #`, pertenece a L(<instruccion>) pero **no** a
L(<programa>). Para una instrucción _w_ se cumple: _w_ ∈ L(<instruccion>) si y solo si
`Begin Programa prueba w End` ∈ L(<programa>).

El informe indica siempre contra qué lenguaje se comprueba cada cadena, y muestra las derivaciones y los árboles tanto
desde `<instruccion>` como desde el símbolo inicial `<programa>`. En el validador, el modo por defecto comprueba L(<programa>)
y `--fragmento` comprueba **exactamente una instrucción** (L(<instruccion>)).

## Cobertura de la rúbrica

- **P1:** terminales por categoría, no terminales, símbolo inicial y G = (V, Σ, P, S) completo, con análisis léxico/sintáctico y gramática léxica a nivel de carácter (Anexo A.1).
- **P2:** producciones en `gramatica.bnf`, diferenciación de las tres instrucciones, función de cada no terminal, verificación del programa de referencia (20 instrucciones, 91 tokens) y aclaración de pertenencia.
- **P3:** derivaciones por la izquierda desde `<instruccion>` y desde `<programa>` (`evidencias/derivaciones.txt`) y dos árboles consistentes con ellas.
- **P4:** ocho casos justificados con el lenguaje comprobado y la posición del error (`evidencias/validacion.json`, Anexo A.2).
- **JFLAP:** gramática ingresada con una letra por símbolo (traducción en el Anexo A.4 del informe); las 11 cadenas de prueba dan el resultado esperado en `lab3_extension.jff`, y `bpiti#e` se rechaza en `lab3_base.jff`.
- **Extensión C:** `entero ID #` y `real ID #`, con gramática, derivación y casos válido/inválido.

Los puntajes indican la distribución de la rúbrica, no una calificación obtenida.

## Ejecutar y verificar

El validador y las pruebas requieren solo Python 3. Los árboles requieren además Graphviz (`dot`).

```bash
python3 validador.py ejemplos/programa_referencia.txt                 # ∈ L(<programa>)
python3 validador.py ejemplos/programa_extendido.txt --extension
python3 validador.py --fragmento --cadena "z = x + y #"               # ∈ L(<instruccion>)
python3 herramientas/derivacion.py --fragmento --desde instruccion --cadena "z = x + y #"
python3 herramientas/derivacion.py --fragmento --desde programa --cadena "z = x + y #"
python3 -m unittest discover -s pruebas -v
python3 herramientas/generar_evidencias.py
```

`evidencias/pruebas.txt` conserva el registro de las 25 pruebas. `generar_evidencias.py` reproduce las 19 comprobaciones
de cadenas, los dos programas completos, las derivaciones y los árboles (JSON, DOT, SVG y PNG).

## Alcance

La gramática base reconoce una o más instrucciones: asignación simple, asignación con una operación aritmética binaria o salida
de un identificador. Operadores: `+`, `-`, `*`, `/` y `%`. La extensión C se activa con `--extension`.

`ID` y `NUM` son categorías de tokens; los lexemas se conservan como anotaciones. Los identificadores empiezan con una letra y
admiten letras, dígitos y guion bajo. Los números no tienen signo e incluyen 0. Las reservadas distinguen mayúsculas.
Se ignoran espacios y comentarios `/* ... */` no anidados. No se realiza evaluación semántica.


## JFLAP

JFLAP solo admite símbolos de una letra: `S`=`<programa>`, `L`=`<lista_instrucciones>`, `I`=`<instruccion>`, `A`=`<asignacion_simple>`, `R`=`<asignacion_aritmetica>`, `E`=`<expresion>`, `O`=`<operando>`, `M`=`<operador>`, `C`=`<salida>`, `D`=`<declaracion>`, `Y`=`<tipo>`; y `b`=Begin, `p`=Programa, `e`=End, `o`=salida, `i`=ID, `n`=NUM, `t`=entero, `r`=real. Cada instrucción se prueba envuelta en `bpi … e` (por ejemplo, `z = x + y #` es `bpii=i+i#e`). Abrir el `.jff` en JFLAP y usar Input → Brute Force Parse o Multiple Brute Force Parse.
