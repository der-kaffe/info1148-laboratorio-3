"""Genera el mismo informe en HTML y PDF a partir de contenidos compartidos."""
from pathlib import Path
from html import escape
from xml.sax.saxutils import escape as xml_escape
import json
import re
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
sys.path.insert(0, str(ROOT))


def p(text):
    return {'tipo': 'p', 'texto': text}


def h(text):
    return {'tipo': 'h', 'texto': text}


def code(text):
    return {'tipo': 'codigo', 'texto': text}


def table(headers, rows, widths=None):
    return {'tipo': 'tabla', 'cabecera': headers, 'filas': rows, 'anchos': widths}


def lista(items):
    return {'tipo': 'lista', 'items': items}


def construir_arbol(arbol):
    lines = ['digraph derivacion {', 'graph [bgcolor="white", ranksep="0.38", nodesep="0.25", pad="0.15"];',
             'node [shape=box, style="rounded,filled", fillcolor="#edf3fb", color="#51749b", fontname="DejaVu Sans", fontsize=12];',
             'edge [color="#5a6c80"];']
    counter = 0

    def add(node):
        nonlocal counter
        idx = f'n{counter}'
        counter += 1
        if 'simbolo' in node:
            label = '<' + node['simbolo'] + '>'
            lines.append(f'{idx} [label={json.dumps(label)}];')
            for child in node.get('hijos', []):
                sub = add(child)
                lines.append(f'{idx} -> {sub};')
        else:
            label = node['lexema']
            if node['token'] in ['ID', 'NUM']:
                label = node['token'] + '[' + label + ']'
            lines.append(f'{idx} [label={json.dumps(label)}, fillcolor="#e9f5ed"];')
        return idx

    add(arbol)
    lines.append('}')
    dot = DOCS / 'arbol_z_x_mas_y.dot'
    dot.write_text('\n'.join(lines) + '\n')
    subprocess.run(['dot', '-Tsvg', str(dot), '-o', str(DOCS / 'arbol_z_x_mas_y.svg')], check=True)
    subprocess.run(['dot', '-Tpng', '-Gdpi=180', str(dot), '-o', str(DOCS / 'arbol_z_x_mas_y.png')], check=True)


def contenido():
    evidence = json.loads((ROOT / 'evidencias/validacion.json').read_text())
    casos = {item['id']: item for item in evidence['casos']}
    referencia = next(item for item in evidence['programas'] if 'referencia' in item['archivo'])
    assert referencia['nodos']['instruccion'] == 20
    grammar = (ROOT / 'gramatica.bnf').read_text()
    # Las primeras nueve producciones agrupadas constituyen la gramática base.
    base = '\n'.join(line for line in grammar.splitlines() if line.startswith('<'))
    base = '\n'.join(base.splitlines()[:9])
    terminales = [
        ['Palabras reservadas', 'Begin, Programa, End, salida', 'Delimitan el programa o introducen una salida.'],
        ['Operadores aritméticos', '+, -, *, /, %', 'Operaciones binarias entre dos operandos.'],
        ['Asignación', '=', 'Separa el identificador destino de su valor o expresión.'],
        ['Símbolo especial', '#', 'Termina una instrucción.'],
        ['Identificadores', 'ID', 'Categoría de nombres como x, z2 y operativo_01_02.'],
        ['Números', 'NUM', 'Categoría de valores como 20, 0 y 1.345.'],
    ]
    nonterminals = [
        ['<programa>', 'Construye un programa completo con cabecera, cuerpo y cierre.'],
        ['<lista_instrucciones>', 'Produce una o más instrucciones, conservando su orden.'],
        ['<instruccion>', 'Selecciona una asignación simple, una aritmética o una salida.'],
        ['<asignacion_simple>', 'Asigna un identificador o un número a un identificador destino.'],
        ['<asignacion_aritmetica>', 'Asigna el resultado sintáctico de una operación binaria.'],
        ['<expresion>', 'Une un operando izquierdo, un operador y un operando derecho.'],
        ['<operando>', 'Selecciona ID o NUM.'],
        ['<operador>', 'Selecciona uno de los cinco operadores aritméticos.'],
        ['<salida>', 'Forma una instrucción salida ID #.'],
    ]
    derivacion_z = '''<instruccion>
⇒ <asignacion_aritmetica>
⇒ ID[z] = <expresion> #
⇒ ID[z] = <operando> <operador> <operando> #
⇒ ID[z] = ID[x] <operador> <operando> #
⇒ ID[z] = ID[x] + <operando> #
⇒ ID[z] = ID[x] + ID[y] #'''
    derivacion_salida = '''<instruccion>
⇒ <salida>
⇒ salida ID[z] #'''
    extension = '''<instruccion> ::= <asignacion_simple> | <asignacion_aritmetica>
                | <salida> | <declaracion>
<declaracion> ::= <tipo> ID "#"
<tipo> ::= "entero" | "real"'''
    validaciones = []
    for n in range(1, 8):
        item = casos[str(n)]
        validaciones.append([str(n), item['texto'], 'Válida' if item['resultado'] else 'Inválida', item['justificacion']])
    validaciones.append(['8', 'Begin / Programa prueba / x = 5 # / salida x # / End',
                         'Depende de la lectura',
                         'Válida al interpretar las barras como separadores editoriales de líneas. Inválida si las barras son caracteres literales del programa.'])
    pruebas = ROOT / 'evidencias/pruebas.txt'
    test_match = re.search(r'Ran (\d+) tests?', pruebas.read_text()) if pruebas.exists() else None
    test_count = test_match[1] if test_match else 'las pruebas incluidas'
    paginas = [
        ('1. Identificación formal de la gramática', [
            p('<b>Laboratorio 3 - Diseño y Validación de Gramáticas</b><br/>Teoría de la Computación · INFO1148 · 21 de octubre de 2026'),
            p('Propuesta de solución al enunciado, con decisiones de diseño explícitas y evidencias ejecutables. La actividad se describe como trabajo en parejas y entrega de informe más evidencias; este documento desarrolla sus preguntas y su extensión C.'),
            h('1. Terminales y clasificación'),
            p('Separamos el análisis léxico del sintáctico. El léxico reconoce nombres y números concretos; la GLC trabaja con sus categorías ID y NUM. Los otros terminales se escriben por su lexema literal.'),
            table(['Clase', 'Terminales', 'Función'], terminales, [0.20, 0.27, 0.53]),
            h('2. No terminales y 3. símbolo inicial'),
            p('V = {<programa>, <lista_instrucciones>, <instruccion>, <asignacion_simple>, <asignacion_aritmetica>, <expresion>, <operando>, <operador>, <salida>}. El símbolo inicial es S = <programa>.'),
            h('4. Definición formal'),
            code('G = (V, Σ, P, S)\nΣ = {Begin, Programa, End, salida, ID, NUM, =, #, +, -, *, /, %}\nS = <programa>'),
            p('V contiene los nueve no terminales anteriores y Σ los trece terminales indicados. V y Σ son disjuntos. P es el conjunto de producciones de la sección 2. Es una GLC porque el lado izquierdo de cada producción es un único no terminal.'),
            p('<b>Notación:</b> se conserva el orden G = (V, Σ, P, S) pedido por el laboratorio. En otros apuntes del curso la misma información se ordena como (V_N, V_T, S, P). Aquí V significa el conjunto de no terminales.'),
            p('<i>Respaldo: enunciado, PDF p. 2, preguntas 1-5; sesion_3_4.pdf, PDF pp. 3 y 8.</i>'),
        ]),
        ('Identificadores, números y decisiones léxicas', [
            h('5. Por qué no enumerar cada nombre o valor'),
            p('Sería insuficiente listar únicamente x, y, z o 20: también se necesitan nombres nuevos y números de longitud arbitraria. Se usan patrones generales, y cada token conserva el lexema concreto como dato asociado. ID y NUM son terminales de categoría de esta GLC; no se añaden reglas ID → x ni NUM → 20.'),
            code('L = [A-Za-zÑñÁÉÍÓÚÜáéíóúü]\nD = [0-9]\nID = L (L | D | "_")*\nNUM = D+ ("." D+)?'),
            lista([
                'Un identificador empieza con una letra; después admite letras, dígitos y guion bajo. Ejemplos: x, z2 y operativo_01_02. La clase L declarada es la convención finita de letras de esta implementación.',
                'Las reservadas exactas son Begin, Programa, End y salida. Se distinguen mayúsculas y minúsculas. Un nombre más largo, como salida_total, sigue siendo un identificador.',
                'NUM admite enteros y reales decimales sin signo: 20, 0 y 1.345. Aunque el enunciado usa la palabra positivos, el programa incluye 0; por ello se interpretan como valores no negativos.',
                'Se requieren dígitos a ambos lados del punto de un real. No se incluyen notación exponencial ni signos unarios.',
                'Los espacios separan componentes y se descartan. Se admiten comentarios /* ... */ no anidados para representar el comentario del programa de referencia. El comentario no se convierte en una instrucción.',
                'En modo de extensión, entero y real se añaden al conjunto de reservadas. real es una palabra de tipo; NUM sigue siendo la categoría de un literal numérico.',
            ]),
            h('Una categoría, muchos lexemas'),
            table(['Texto', 'Lectura sintáctica'], [
                ['x = 20 #', 'ID[x] = NUM[20] #'],
                ['z = x + y #', 'ID[z] = ID[x] + ID[y] #'],
                ['salida temporal #', 'salida ID[temporal] #'],
            ], [0.40, 0.60]),
            p('En ID[z], el símbolo terminal es ID y z es su lexema anotado. Esta notación no añade un nuevo terminal por cada nombre. Los corchetes son explicativos y no se escriben en el programa.'),
            p('<i>Respaldo: enunciado, PDF pp. 1-2; los patrones y la separación de fases son decisiones explícitas de esta propuesta.</i>'),
        ]),
        ('2. Construcción de la GLC', [
            h('6. Producciones de la gramática base'), code(base),
            h('7. Diferencia entre las tres instrucciones'),
            table(['Construcción', 'Forma', 'Ejemplo'], [
                ['Asignación simple', 'ID = <operando> #', 'temporal = x #'],
                ['Asignación aritmética', 'ID = <operando> <operador> <operando> #', 'z = x + y #'],
                ['Salida', 'salida ID #', 'salida z #'],
            ], [0.24, 0.48, 0.28]),
            p('Las alternativas son distinguibles: después del primer operando, # cierra una asignación simple; un operador seguido de otro operando forma una asignación aritmética. salida inicia la tercera clase.'),
            h('8. Función de los no terminales'),
            table(['No terminal', 'Función'], nonterminals, [0.34, 0.66]),
            p('La lista nunca produce ε: tiene la alternativa de una instrucción y otra que agrega una instrucción delante de una lista. Así permite cualquier cantidad positiva de instrucciones.'),
            p('<i>Respaldo: enunciado, PDF pp. 2-3, pregunta 2.</i>'),
        ]),
        ('Verificación del programa de referencia', [
            h('9. El programa completo queda representado'),
            p('La cabecera se reconoce como Begin Programa ID[operativo_01_02], la lista contiene veinte instrucciones y el cierre es End. Tras descartar el comentario y los espacios, cada instrucción coincide con una de las tres alternativas de la gramática.'),
            table(['Clase', 'Cantidad', 'Evidencia del programa'], [
                ['Asignaciones simples', '6', 'x = 1.345 #; y = 20 #; temporal = 0 #; temporal = x #; x = y #; y = temporal #'],
                ['Asignaciones aritméticas', '7', 'z y z2 usan +; h y h2 usan -; k usa *; t usa /; m usa %.'],
                ['Salidas', '7', 'Se imprimen z, h, k, t, m, x e y.'],
                ['Total', '20', 'Las veinte instrucciones terminan en #.'],
            ], [0.27, 0.13, 0.60]),
            p('El validador acepta el archivo completo ejemplos/programa_referencia.txt desde el símbolo inicial <programa>. La evidencia registra ' + str(referencia['cantidad_tokens']) + ' tokens y los veinte nodos <instruccion> del árbol.'),
            h('Alcance elegido'),
            p('La asignación aritmética contiene exactamente una operación binaria. Esta elección sencilla cubre las estructuras mínimas y todos los ejemplos pedidos. No se agregan paréntesis ni operaciones encadenadas; por ello no hace falta fijar precedencia entre varios operadores de una misma expresión.'),
            table(['Cadena adicional', 'Resultado', 'Razón'], [
                ['x = a + b * c #', 'Inválida', 'Contiene dos operadores en una sola expresión.'],
                ['x = -1 #', 'Inválida', 'No se definió signo unario.'],
                ['Begin Programa prueba End', 'Inválida', 'La lista debe contener al menos una instrucción.'],
            ], [0.43, 0.17, 0.40]),
            p('Este es un análisis sintáctico. No se calcula el valor de k / z ni se comprueba si una variable fue declarada o si una división puede dar error al ejecutarse.'),
            p('<i>Respaldo: programa de referencia del enunciado, PDF pp. 1-2; evidencia ejecutada en evidencias/validacion.json.</i>'),
        ]),
        ('3. Derivaciones por la izquierda', [
            p('En cada paso se sustituye el no terminal situado más a la izquierda. Como S = <programa> genera programas completos, las instrucciones aisladas de los puntos 10 y 11 se derivan localmente desde <instruccion>.'),
            h('10. Derivación de z = x + y #'), code(derivacion_z),
            p('<b>Realización léxica de la última fila:</b> z = x + y #. Las elecciones z, x e y son los valores de los tokens ID; no son nuevas producciones.'),
            h('11. Derivación de salida z #'), code(derivacion_salida),
            p('<b>Realización léxica:</b> salida z #.'),
            h('Cómo se integran en una derivación desde S'),
            code('<programa>\n⇒ Begin Programa ID[prueba] <lista_instrucciones> End\n⇒ Begin Programa ID[prueba] <instruccion> End'),
            p('A partir de esa última forma se aplica cualquiera de las derivaciones locales anteriores. El resultado es un programa completo de una instrucción. Una instrucción aislada es un fragmento válido; no se afirma que por sí sola pertenezca al lenguaje completo generado desde <programa>.'),
            p('<i>Respaldo: enunciado, PDF p. 3, puntos 10-11; las derivaciones se calculan con las producciones de la sección 2.</i>'),
        ]),
        ('Árbol sintáctico y tres cadenas adicionales', [
            h('12. Árbol de z = x + y #'), {'tipo': 'figura'},
            p('Árbol generado desde la misma estructura que devuelve el validador. Se adjuntan el archivo DOT editable y sus representaciones SVG y PNG. La herramienta utilizada es Graphviz; no se utilizó JFLAP.'),
            h('13. Relación entre raíz, nodos y hojas'),
            lista([
                'La raíz es <instruccion>, porque el árbol representa una instrucción aislada. En un árbol del programa completo la raíz sería <programa>.',
                'Los nodos internos son no terminales. Cada conjunto de hijos corresponde exactamente al lado derecho de una producción aplicada a su padre.',
                'Las hojas, de izquierda a derecha, son ID[z], =, ID[x], +, ID[y], #. Al conservar sus lexemas se obtiene z = x + y #.',
                'Los corchetes identifican los lexemas asociados a ID; no son símbolos adicionales de entrada.',
            ]),
            h('14. Comprobación de las tres cadenas'),
            table(['Cadena', '¿Se genera como instrucción?', 'Justificación'], [
                ['x = 20 #', 'Sí', '<asignacion_simple>, con ID[x] y <operando> → NUM[20].'],
                ['z = x * y #', 'Sí', '<asignacion_aritmetica>, con operandos ID[x], ID[y] y <operador> → *.'],
                ['salida temporal #', 'Sí', '<salida> → salida ID[temporal] #.'],
            ], [0.28, 0.22, 0.50]),
            p('<i>Respaldo: enunciado, PDF p. 3, puntos 12-14; árbol y justificaciones derivados de la gramática propuesta.</i>'),
        ]),
        ('4. Validación y detección de errores', [
            p('Los casos 1-7 se comprueban como instrucciones. El caso 8 se comprueba como programa completo. La tabla indica tanto la aceptación como el elemento que falta o está fuera de lugar.'),
            table(['Caso', 'Cadena', 'Resultado', 'Análisis'], validaciones, [0.07, 0.28, 0.18, 0.47]),
            h('La doble lectura del caso 8'),
            p('Se conserva la cadena original en el archivo de casos y se añade un ejemplo separado con saltos de línea. La barra / no se transforma globalmente: dentro de una expresión representa división y dentro de /* ... */ participa en la delimitación del comentario.'),
            code('Begin\nPrograma prueba\nx = 5 #\nsalida x #\nEnd'),
            p('La versión anterior con líneas es válida. La versión literal Begin / Programa ... se rechaza al encontrar / donde la producción exige Programa. Ambas comprobaciones aparecen por separado en la evidencia.'),
            p('<i>Respaldo: tabla de ocho casos del enunciado, PDF p. 3; resultados en evidencias/validacion.json.</i>'),
        ]),
        ('5. Extensión creativa: declaraciones de variables', [
            p('Se elige la <b>opción C</b>: añadir declaraciones sencillas. Su utilidad sintáctica es permitir que el programa exprese un tipo y un nombre antes de las asignaciones.'),
            h('Sintaxis y modificación formal'), code(extension),
            p('Los nuevos terminales son entero y real. Los nuevos no terminales son <declaracion> y <tipo>. <declaracion> construye la instrucción completa; <tipo> elige uno de los dos tipos.'),
            code("G_ext = (V_ext, Σ_ext, P_ext, S)\nV_ext = V ∪ {<declaracion>, <tipo>}\nΣ_ext = Σ ∪ {entero, real}\nS = <programa>"),
            p('P_ext conserva las reglas base, reemplaza la alternativa de <instruccion> por la versión ampliada y añade las reglas de <declaracion> y <tipo> anteriores. La lista sigue exigiendo al menos una instrucción.'),
            h('Cadena válida e inválida'),
            table(['Cadena', 'Resultado', 'Justificación'], [
                ['entero edad #', 'Válida', 'Tiene tipo, identificador y terminador.'],
                ['entero #', 'Inválida', 'Falta el identificador después del tipo.'],
            ], [0.28, 0.18, 0.54]),
            h('Derivación por la izquierda'),
            code('<instruccion>\n⇒ <declaracion>\n⇒ <tipo> ID[edad] #\n⇒ entero ID[edad] #'),
            p('La realización textual es entero edad #. Este fragmento puede ocupar cualquier posición de <instruccion> dentro del programa. El archivo programa_extendido.txt incluye declaraciones enteras y reales, asignaciones y salidas.'),
            p('La extensión define sintaxis, no una tabla de símbolos: no comprueba repetición de declaraciones, declaración previa ni compatibilidad de tipos. La palabra reservada real designa el tipo; 20.5 se reconoce como NUM.'),
            p('<i>Respaldo: opción C y requisitos de la extensión del enunciado, PDF p. 4.</i>'),
        ]),
        ('6. Evidencias, reproducción y conclusiones', [
            h('Evidencias entregadas'),
            lista([
                'Informe HTML y PDF con identificación formal, producciones, derivaciones, árbol, validación, extensión y conclusiones.',
                'gramatica.bnf contiene las nueve producciones agrupadas de la base y la modificación de la extensión C.',
                'validador.py contiene el análisis léxico y sintáctico; devuelve errores con fase, línea y columna.',
                'evidencias/validacion.json registra once comprobaciones de cadenas, incluidas ambas lecturas del caso 8 y los dos ejemplos de extensión, más los dos programas completos aceptados.',
                'evidencias/arbol_z_x_mas_y.json conserva el árbol que sirve de fuente de la figura.',
                'evidencias/pruebas.txt registra la ejecución de ' + str(test_count) + ' pruebas automatizadas; el código de esas pruebas se incluye en pruebas/.',
            ]),
            h('Cómo repetir la comprobación'),
            code('python3 validador.py ejemplos/programa_referencia.txt\npython3 validador.py --fragmento --cadena "z = x + y #"\npython3 validador.py ejemplos/programa_extendido.txt --extension\npython3 -m unittest discover -s pruebas -v\npython3 herramientas/generar_evidencias.py'),
            h('Conclusiones'),
            p('La GLC propuesta distingue programas completos de instrucciones y separa asignaciones simples, asignaciones con una operación y salidas. ID y NUM permiten reutilizar las mismas producciones con distintos nombres y valores. Las veinte instrucciones del programa de referencia quedan cubiertas y los errores de los casos 4-7 se detectan por un elemento sintáctico concreto.'),
            p('Las derivaciones, el árbol y el validador comparten las mismas producciones. La extensión agrega declaraciones mediante dos nuevos no terminales y dos palabras reservadas, conservando la estructura del programa. Las decisiones sobre 0, comentarios y barras editoriales se declaran para que el alcance de la solución sea verificable.'),
            h('Fuentes'),
            p('1. Laboratorio_3_enunciado.pdf, copia del documento de cinco páginas proporcionado para esta actividad. Pregunta 1: p. 2; pregunta 2: pp. 2-3; pregunta 3 y ocho casos: p. 3; extensión y entregables: p. 4; coherencia exigida: p. 5.'),
            p('2. sesion_3_4.pdf, archivo del curso: definición de gramática en PDF p. 3 y definición de L(G) en PDF p. 8. Enlace: https://educa.blackboard.com/ultra/courses/_40866_1/file/_4454745_1?courseId=_40866_1'),
            p('Los desarrollos concretos de esta entrega son una propuesta propia; los archivos de referencia establecen el problema y sus conceptos.'),
        ]),
        ('Anexo: programa de referencia validado', [
            p('Transcripción del programa que aparece entre las páginas 1 y 2 del enunciado. Se excluyen el encabezado y la numeración editorial de página; el comentario se conserva.'),
            code((ROOT / 'ejemplos/programa_referencia.txt').read_text()),
        ]),
    ]
    return paginas


def generar_html(paginas):
    def block(b):
        kind = b['tipo']
        if kind in ['p', 'h']:
            tag = 'p' if kind == 'p' else 'h3'
            text = b['texto'] if kind == 'p' else escape(b['texto'])
            return f'<{tag}>{text}</{tag}>'
        if kind == 'codigo':
            return '<pre><code>' + escape(b['texto']) + '</code></pre>'
        if kind == 'lista':
            return '<ul>' + ''.join('<li>' + escape(x) + '</li>' for x in b['items']) + '</ul>'
        if kind == 'figura':
            return '<figure><img src="arbol_z_x_mas_y.svg" alt="Árbol de la instrucción z = x + y #"><figcaption>Las hojas verdes son los terminales; los nodos azules son no terminales.</figcaption></figure>'
        return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th>' + escape(x) + '</th>' for x in b['cabecera']) + '</tr></thead><tbody>' + ''.join(
            '<tr>' + ''.join('<td>' + escape(str(x)) + '</td>' for x in row) + '</tr>' for row in b['filas']) + '</tbody></table></div>'

    article = ''.join('<section id="s' + str(i) + '"><h2>' + escape(title) + '</h2>' + ''.join(block(b) for b in blocks) + '</section>' for i, (title, blocks) in enumerate(paginas, 1))
    nav = ''.join(f'<a href="#s{i}">{escape(title)}</a>' for i, (title, _) in enumerate(paginas, 1))
    html = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Laboratorio 3 - Diseño y Validación de Gramáticas</title><style>
:root{color-scheme:light;--bg:#f3f6fa;--paper:#fff;--text:#213046;--muted:#56657a;--line:#d4deea;--accent:#185796;--code:#edf3fa}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 system-ui,sans-serif}html{scroll-behavior:smooth;scroll-padding-top:6rem}a{color:var(--accent)}header{position:sticky;top:0;padding:.7rem 1.2rem;background:var(--paper);border-bottom:1px solid var(--line);display:flex;gap:1rem;align-items:center;justify-content:space-between;z-index:3}header div{display:flex;gap:.5rem;flex-wrap:wrap}button{font:inherit;padding:.4rem .7rem;border:1px solid var(--line);border-radius:7px;background:var(--paper);color:var(--text);cursor:pointer}button:hover{border-color:var(--accent)}button:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}.layout{display:grid;grid-template-columns:230px minmax(0,1fr);max-width:1350px;margin:auto;gap:2rem;padding:2rem 1.3rem}aside{position:sticky;top:6rem;align-self:start;font-size:.88rem}aside a{display:block;margin:.6rem 0;text-decoration:none}main{min-width:0}h1{font-size:clamp(2rem,4vw,3rem);line-height:1.2}h2{font-size:1.7rem;line-height:1.3;margin-top:0}h3{font-size:1.15rem;margin-top:1.4rem}section{padding:1.7rem;background:var(--paper);border:1px solid var(--line);border-radius:12px;margin-bottom:1.5rem}p{margin:.85rem 0}pre{background:var(--code);padding:1rem;border-radius:7px;overflow:auto;font:14px/1.65 ui-monospace,monospace}li{margin:.6rem 0}.table-wrap{overflow:auto;margin:1rem 0}table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{padding:.6rem .7rem;text-align:left;border:1px solid var(--line);vertical-align:top}th{background:var(--code)}figure{margin:1rem 0;background:white;padding:.7rem;border-radius:8px}figure img{width:100%;height:auto}figcaption{color:#4b5c70;font-size:.86rem}.muted{color:var(--muted)}[hidden]{display:none!important}body.full .layout{grid-template-columns:1fr;max-width:1100px}:root[data-theme=dark]{color-scheme:dark;--bg:#101823;--paper:#192637;--text:#e6edf5;--muted:#b6c5d7;--line:#42546a;--accent:#98c9ff;--code:#27394f}@media(max-width:850px){.layout{grid-template-columns:1fr;padding:1rem}aside{position:static}aside a{display:inline-block;margin:.3rem .7rem .3rem 0}section{padding:1rem}header{align-items:flex-start}header strong{max-width:12rem}body{font-size:16px}}@media print{:root,:root[data-theme=dark]{--paper:#fff;--bg:#fff;--text:#111;--line:#bbb;--code:#f2f2f2}header,aside{display:none}.layout{display:block;padding:0}section{border:0;padding:.3rem 0;break-before:page}section:first-of-type{break-before:auto}pre{white-space:pre-wrap;font-size:10px}h2,h3{break-after:avoid}tr,figure{break-inside:avoid}a{color:#111}}
</style></head><body><header><strong>Laboratorio 3 · INFO1148</strong><div><button id="indice" aria-expanded="true" aria-controls="nav">Ocultar índice</button><button id="tema" aria-pressed="false">Modo nocturno</button><button id="imprimir">Imprimir</button></div></header><div class="layout"><aside id="nav"><b>Contenido</b>__NAV__<p><a href="Informe_Laboratorio_3.pdf">Descargar informe PDF</a></p><p><a href="Laboratorio_3_enunciado.pdf">Abrir enunciado original</a></p></aside><main><h1>Diseño y validación de una GLC</h1><p class="muted">Desarrollo completo, extensión C y evidencias reproducibles.</p>__ARTICLE__</main></div><script>
const theme = document.getElementById('tema');let saved=null;try{saved=localStorage.getItem('info1148-theme')}catch{}function setTheme(dark){document.documentElement.dataset.theme=dark?'dark':'light';theme.setAttribute('aria-pressed',String(dark))}setTheme(saved?saved==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches);theme.onclick=()=>{const dark=document.documentElement.dataset.theme!=='dark';setTheme(dark);try{localStorage.setItem('info1148-theme',dark?'dark':'light')}catch{}};document.getElementById('indice').onclick=()=>{const nav=document.getElementById('nav');nav.hidden=!nav.hidden;document.body.classList.toggle('full',nav.hidden);const b=document.getElementById('indice');b.textContent=nav.hidden?'Mostrar índice':'Ocultar índice';b.setAttribute('aria-expanded',String(!nav.hidden))};document.getElementById('imprimir').onclick=()=>window.print();
</script></body></html>'''.replace('__NAV__', nav).replace('__ARTICLE__', article)
    # Los ángulos de los no terminales son texto, no etiquetas HTML.
    html = re.sub(r'<(programa|lista_instrucciones|instruccion|asignacion_simple|asignacion_aritmetica|expresion|operando|operador|salida|declaracion|tipo)>', r'&lt;\1&gt;', html)
    (DOCS / 'Informe_Laboratorio_3.html').write_text(html)


def generar_pdf(paginas):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Table, TableStyle, Image, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_LEFT
    font_root = Path('/usr/share/fonts/truetype/dejavu')
    for name, file in [('Body','DejaVuSans.ttf'), ('Body-Bold','DejaVuSans-Bold.ttf'), ('Body-Italic','DejaVuSans-Oblique.ttf'), ('Mono','DejaVuSansMono.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_root / file)))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='Body-Bold', italic='Body-Italic', boldItalic='Body-Bold')
    styles = getSampleStyleSheet()
    body = ParagraphStyle('Texto', fontName='Body', fontSize=9.2, leading=13.7, spaceAfter=8)
    title = ParagraphStyle('Titulo', fontName='Body-Bold', fontSize=17, leading=22, textColor=colors.HexColor('#194b7b'), spaceAfter=15)
    sub = ParagraphStyle('Subtitulo', parent=body, fontName='Body-Bold', fontSize=11.2, leading=15, spaceBefore=8, spaceAfter=7, keepWithNext=True)
    cell = ParagraphStyle('Celda', parent=body, fontSize=8.0, leading=11.5, spaceAfter=0)
    head_cell = ParagraphStyle('Cabecera', parent=cell, fontName='Body-Bold')
    monospace = ParagraphStyle('Codigo', fontName='Mono', fontSize=8.1, leading=11.5, spaceBefore=4, spaceAfter=11, backColor=colors.HexColor('#f0f4f9'), borderPadding=7)
    doc = SimpleDocTemplate(str(DOCS / 'Informe_Laboratorio_3.pdf'), pagesize=A4, rightMargin=40, leftMargin=40, topMargin=45, bottomMargin=43,
                            title='Laboratorio 3 - Diseño y Validación de Gramáticas', author='Solución propuesta - INFO1148')
    width = A4[0] - 80
    story = []

    def markup(text):
        # Se escapan los no terminales y los caracteres XML antes de restaurar
        # las pocas etiquetas de formato que usa el contenido controlado.
        text = xml_escape(text)
        for tag in ['b', '/b', 'i', '/i', 'br/']:
            text = text.replace(xml_escape('<' + tag + '>'), '<' + tag + '>')
        return text

    for page_idx, (heading, blocks) in enumerate(paginas):
        if page_idx:
            story.append(PageBreak())
        story.append(Paragraph(xml_escape(heading), title))
        for b in blocks:
            if b['tipo'] == 'p':
                story.append(Paragraph(markup(b['texto']), body))
            elif b['tipo'] == 'h':
                story.append(Paragraph(xml_escape(b['texto']), sub))
            elif b['tipo'] == 'codigo':
                lines = []
                for line in b['texto'].splitlines():
                    lines.extend(textwrap.wrap(line, width=98, break_long_words=False, break_on_hyphens=False, subsequent_indent='    ') or [''])
                story.append(Preformatted('\n'.join(lines), monospace))
            elif b['tipo'] == 'lista':
                for item in b['items']:
                    story.append(Paragraph('• ' + xml_escape(item), body))
            elif b['tipo'] == 'figura':
                from PIL import Image as PILImage
                path = DOCS / 'arbol_z_x_mas_y.png'
                with PILImage.open(path) as img:
                    w, ht = img.size
                ratio = min(width / w, 260 / ht)
                story.append(Image(str(path), width=w * ratio, height=ht * ratio))
                story.append(Spacer(1, 9))
            elif b['tipo'] == 'tabla':
                rows = [[Paragraph(xml_escape(str(x)), head_cell) for x in b['cabecera']]]
                rows += [[Paragraph(xml_escape(str(x)), cell) for x in row] for row in b['filas']]
                widths = [width * x for x in b['anchos']] if b['anchos'] else None
                tab = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
                tab.setStyle(TableStyle([
                    ('VALIGN',(0,0),(-1,-1),'TOP'), ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cad5e1')),
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f0f8')),
                    ('LEFTPADDING',(0,0),(-1,-1),6), ('RIGHTPADDING',(0,0),(-1,-1),6),
                    ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
                ]))
                story.extend([tab, Spacer(1, 10)])

    def footer(canvas, _):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#d5dfe9'))
        canvas.line(40, 32, A4[0] - 40, 32)
        canvas.setFillColor(colors.HexColor('#52677e'))
        canvas.setFont('Body', 8)
        canvas.drawString(40, 20, 'INFO1148 · Laboratorio 3 · Propuesta de solución')
        canvas.drawRightString(A4[0] - 40, 20, str(canvas.getPageNumber()))
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    DOCS.mkdir(exist_ok=True)
    tree = json.loads((ROOT / 'evidencias/arbol_z_x_mas_y.json').read_text())
    construir_arbol(tree)
    pages = contenido()
    generar_html(pages)
    generar_pdf(pages)
    print('Informe HTML/PDF y árbol DOT/SVG/PNG generados desde los mismos contenidos.')


if __name__ == '__main__':
    main()
