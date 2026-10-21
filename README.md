# Laboratorio 3: Diseño y Validación de Gramáticas

Teoría de la Computación · INFO1148

**Autores: Juan Cárdenas y Bayron Flores.**

## Informe y entrega

- [Informe PDF](docs/Informe_Laboratorio_3.pdf) (formato de la plantilla del laboratorio, secciones 1 a 5 y anexo)
- [Informe editable (.docx)](docs/Informe_Laboratorio_3.docx)
- [Gramática base, extensión y gramática léxica](gramatica.bnf)
- Árboles de derivación de `z = x + y #`: [desde `<instruccion>`](arbol_sintactico/arbol_z_x_mas_y.svg) y [desde `<programa>`](arbol_sintactico/arbol_z_x_mas_y_programa.svg) (también `.png` y `.dot`)
- [Derivaciones por la izquierda](evidencias/derivaciones.txt) y [resultados de validación](evidencias/validacion.json)
- [Entrega completa en Google Drive](https://drive.google.com/drive/folders/1SXU1cSjy1-m_Fg0xZlNUexpftVtnUft6?usp=sharing)

## Pertenencia: L(<programa>) y L(<instruccion>)

El símbolo inicial es `<programa>`, así que el lenguaje generado es L(G) = L(<programa>): **solo programas completos**
(`Begin Programa … End`). Una instrucción suelta, como `z = x + y #`, pertenece a L(<instruccion>) pero **no** a
L(<programa>). Para una instrucción *w* se cumple: *w* ∈ L(<instruccion>) si y solo si
`Begin Programa prueba w End` ∈ L(<programa>).

El informe indica siempre contra qué lenguaje se comprueba cada cadena, y muestra las derivaciones y los árboles tanto
desde `<instruccion>` como desde el símbolo inicial `<programa>`. En el validador, el modo por defecto comprueba L(<programa>)
y `--fragmento` comprueba **exactamente una instrucción** (L(<instruccion>)).

## Cobertura de la rúbrica

- **P1:** terminales por categoría, no terminales, símbolo inicial y G = (V, Σ, P, S) completo, con análisis léxico/sintáctico y gramática léxica a nivel de carácter (Anexo A.1).
- **P2:** producciones en `gramatica.bnf`, diferenciación de las tres instrucciones, función de cada no terminal, verificación del programa de referencia (20 instrucciones, 91 tokens) y aclaración de pertenencia.
- **P3:** derivaciones por la izquierda desde `<instruccion>` y desde `<programa>` (`evidencias/derivaciones.txt`) y dos árboles consistentes con ellas.
- **P4:** ocho casos justificados con el lenguaje comprobado y la posición del error (`evidencias/validacion.json`, Anexo A.2).
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

## Regenerar el informe

El informe se rellena sobre la plantilla del curso con las derivaciones y los resultados del validador:

```bash
python3 herramientas/generar_evidencias.py
python3 docs/fuente/generar_informe_desde_plantilla.py docs/fuente/Formato_Informe_LAB_3.docx \
        arbol_sintactico/arbol_z_x_mas_y.png evidencias docs/Informe_Laboratorio_3.docx
soffice --headless --convert-to pdf --outdir docs docs/Informe_Laboratorio_3.docx
```

Requiere `python-docx` y LibreOffice (solo para convertir a PDF).

## Alcance

La gramática base reconoce una o más instrucciones: asignación simple, asignación con una operación aritmética binaria o salida
de un identificador. Operadores: `+`, `-`, `*`, `/` y `%`. La extensión C se activa con `--extension`.

`ID` y `NUM` son categorías de tokens; los lexemas se conservan como anotaciones. Los identificadores empiezan con una letra y
admiten letras, dígitos y guion bajo. Los números no tienen signo e incluyen 0. Las reservadas distinguen mayúsculas.
Se ignoran espacios y comentarios `/* ... */` no anidados. No se realiza evaluación semántica.
