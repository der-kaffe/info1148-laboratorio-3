"""Reproduce la validación de las cadenas del enunciado, sin modificar sus textos."""
from pathlib import Path
from collections import Counter
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validador import validate


def contar_nodos(arbol):
    counts = Counter()
    if isinstance(arbol, dict):
        if 'simbolo' in arbol:
            counts[arbol['simbolo']] += 1
        for child in arbol.get('hijos', []):
            counts.update(contar_nodos(child))
    return counts


def generar():
    casos = json.loads((ROOT / 'ejemplos/casos_validacion.json').read_text())
    resultados = []
    for caso in casos:
        resultado = validate(caso['texto'], fragment=caso['fragmento'], extension=caso['extension'])
        coincide = resultado['valido'] == caso['esperado']
        assert coincide, caso['id']
        resultados.append({**caso, 'resultado': resultado['valido'], 'coincide': coincide,
                           'tokens': resultado['tokens'], 'error': resultado['error']})
    programas = []
    for archivo, extension in [('programa_referencia.txt', False), ('programa_extendido.txt', True)]:
        resultado = validate((ROOT / 'ejemplos' / archivo).read_text(), extension=extension)
        assert resultado['valido'], resultado['error']
        programas.append({'archivo': 'ejemplos/' + archivo, 'extension': extension, 'valido': True,
                          'cantidad_tokens': len(resultado['tokens']),
                          'nodos': dict(contar_nodos(resultado['arbol']))})
    instruccion = validate('z = x + y #', fragment=True)
    assert instruccion['valido']
    evidencia = {'gramatica': 'gramatica.bnf', 'casos': resultados, 'programas': programas,
                 'alcance': 'Sintaxis de programas o instrucciones según el modo; sin evaluación semántica.'}
    target = ROOT / 'evidencias'
    target.mkdir(exist_ok=True)
    (target / 'validacion.json').write_text(json.dumps(evidencia, ensure_ascii=False, indent=2) + '\n')
    (target / 'arbol_z_x_mas_y.json').write_text(json.dumps(instruccion['arbol'], ensure_ascii=False, indent=2) + '\n')
    print(f'{len(resultados)} comprobaciones de casos coinciden; {len(programas)} programas aceptados.')
    for programa in programas:
        print(programa['archivo'], programa['nodos'])


if __name__ == '__main__':
    generar()
