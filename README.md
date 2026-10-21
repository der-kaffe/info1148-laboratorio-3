# Laboratorio 3: Diseño y Validación de Gramáticas

Teoría de la Computación · INFO1148

**Autores: Juan Cárdenas y Bayron Flores.**

## Informe y entrega

- [Informe PDF](docs/Informe_Laboratorio_3.pdf)
- [Fuente LaTeX autónoma](docs/Informe_Laboratorio_3.tex)
- [Entrega completa en Google Drive](https://drive.google.com/drive/folders/1bNQcTqB4XKDPTkW4AXRuGCijnVxjX7TX): PDF, LaTeX y ZIP con las evidencias y los anexos citados en el informe.

Este repositorio conserva 13 archivos del núcleo de la entrega: informe, gramática, validador, programas de ejemplo, casos y evidencias reproducibles. Los documentos docentes, el HTML, las figuras externas y las herramientas de edición del informe se conservan en el paquete completo de Drive.

## Cobertura de la rúbrica

- **P1 (20 puntos):** terminales, no terminales, símbolo inicial y definición G = (V, Σ, P, S), explicados en el informe.
- **P2 (30 puntos):** producciones de `gramatica.bnf`, instrucciones múltiples y programa de referencia completo.
- **P3 (25 puntos):** derivaciones por la izquierda y árbol incluidos en el informe; estructura original en `evidencias/arbol_z_x_mas_y.json`.
- **P4 (25 puntos):** ocho casos justificados en el informe, con resultados y errores en `evidencias/validacion.json`.
- **Extensión C:** declaraciones `entero ID #` y `real ID #`, con gramática, derivación y casos válido/inválido.

Los puntajes indican la distribución de la rúbrica, no una calificación obtenida.

## Ejecutar y verificar

El validador y las pruebas requieren sólo Python 3, sin paquetes adicionales.

```bash
python3 validador.py ejemplos/programa_referencia.txt
python3 validador.py ejemplos/programa_extendido.txt --extension
python3 validador.py --fragmento --cadena "z = x + y #"
python3 -m unittest discover -s pruebas -v
python3 herramientas/generar_evidencias.py
```

`evidencias/pruebas.txt` conserva el registro de las 20 pruebas. El generador reproduce once comprobaciones de cadenas y los dos programas completos.

El caso 8 se valida de dos maneras: con saltos de línea es válido; con barras `/` literales es inválido. Ambas entradas están en `ejemplos/casos_validacion.json`. El analizador nunca sustituye las barras por saltos de línea.

## Alcance

La gramática base reconoce una o más instrucciones de asignación simple, una operación aritmética binaria por asignación o salida de un identificador. Operadores: `+`, `-`, `*`, `/` y `%`. La extensión C se activa con `--extension`.

`ID` y `NUM` son categorías de tokens; los lexemas se conservan como anotaciones. Los identificadores empiezan con una letra y admiten letras, dígitos y guion bajo. Los números no tienen signo e incluyen 0. Las reservadas distinguen mayúsculas. Se ignoran espacios y comentarios `/* ... */` no anidados. No se realiza evaluación semántica.

El archivo LaTeX incluye el árbol con TikZ y puede compilarse por sí solo con pdfLaTeX. Los materiales docentes citados mantienen su autoría y condiciones de uso.
