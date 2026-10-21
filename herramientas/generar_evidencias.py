"""Reproduce la validación de las cadenas del enunciado y las derivaciones del informe.

Genera en evidencias/: validacion.json, arbol_z_x_mas_y.json (raíz <instruccion>),
arbol_z_x_mas_y_programa.json (raíz <programa>) y derivaciones.txt.
Si Graphviz está instalado, también regenera arbol_sintactico/ (DOT, SVG y PNG).
"""
from pathlib import Path
from collections import Counter
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'herramientas'))
from validador import validate
from derivacion import derivar_texto, formatear
import generar_arbol


def contar_nodos(arbol):
    counts = Counter()
    if isinstance(arbol, dict):
        if 'simbolo' in arbol:
            counts[arbol['simbolo']] += 1
        for child in arbol.get('hijos', []):
            counts.update(contar_nodos(child))
    return counts


def generar():
    casos = json.loads((ROOT / 'ejemplos/casos_validacion.json').read_text(encoding='utf-8'))
    resultados = []
    for caso in casos:
        resultado = validate(caso['texto'], fragment=caso['fragmento'], extension=caso['extension'])
        coincide = resultado['valido'] == caso['esperado']
        assert coincide, caso['id']
        resultados.append({**caso, 'lenguaje': resultado['lenguaje'], 'resultado': resultado['valido'], 'coincide': coincide,
                           'tokens': [t for t in resultado['tokens']], 'error': resultado['error']})
    programas = []
    for archivo, extension in [('programa_referencia.txt', False), ('programa_extendido.txt', True)]:
        resultado = validate((ROOT / 'ejemplos' / archivo).read_text(encoding='utf-8'), extension=extension)
        assert resultado['valido'], resultado['error']
        programas.append({'archivo': 'ejemplos/' + archivo, 'extension': extension, 'valido': True,
                          'cantidad_tokens': len(resultado['tokens']),
                          'nodos': dict(contar_nodos(resultado['arbol']))})
    evidencia = {'gramatica': 'gramatica.bnf', 'casos': resultados, 'programas': programas,
                 'convencion': 'L(G) = L(<programa>) contiene solo programas (S = <programa>). Una instrucción '
                               'suelta w se comprueba contra L(<instruccion>); se cumple w en L(<instruccion>) si y solo si '
                               '"Begin Programa prueba w End" pertenece a L(<programa>).',
                 'alcance': 'Sintaxis; sin evaluación semántica.'}
    target = ROOT / 'evidencias'
    target.mkdir(exist_ok=True)
    (target / 'validacion.json').write_text(json.dumps(evidencia, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for nombre, arbol in (('arbol_z_x_mas_y', generar_arbol.arbol_instruccion()),
                          ('arbol_z_x_mas_y_programa', generar_arbol.arbol_programa())):
        (target / f'{nombre}.json').write_text(json.dumps(arbol, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    bloques = []
    for titulo, texto, ext in [('z = x + y #', 'z = x + y #', False), ('salida z #', 'salida z #', False),
                               ('entero edad # (extensión C)', 'entero edad #', True)]:
        for desde in ('instruccion', 'programa'):
            pasos = derivar_texto(texto, fragmento=True, extension=ext, desde=desde)
            complemento = ' (dentro de Begin Programa prueba … End)' if desde == 'programa' else ''
            bloques.append(f'Derivación por la izquierda de «{titulo}» desde <{desde}>{complemento}:\n'
                           + formatear(pasos) + '\n')
    (target / 'derivaciones.txt').write_text('\n'.join(bloques), encoding='utf-8')
    if shutil.which('dot'):
        generar_arbol.generar(ROOT / 'arbol_sintactico')
    print(f'{len(resultados)} comprobaciones de casos coinciden; {len(programas)} programas aceptados.')
    for p in programas:
        print(p['archivo'], p['cantidad_tokens'], 'tokens', p['nodos'])


if __name__ == '__main__':
    generar()
