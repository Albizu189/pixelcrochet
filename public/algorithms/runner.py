"""Application adapter for the unmodified thesis notebook cell.

Only configuration assignments and natural-language instruction strings are
substituted. Every algorithmic statement remains in original_cell.py.
"""
from pathlib import Path
import base64
import builtins
import contextlib
import hashlib
import io
import json
import re
import sys
import types

import cv2
import numpy as np

SOURCE_PATH = Path('/home/pyodide/original_cell.py')
if not SOURCE_PATH.exists():
    SOURCE_PATH = Path(__file__).resolve().with_name('original_cell.py')
SOURCE = SOURCE_PATH.read_text(encoding='utf-8')
CURRENT_PARAMS = {}


class _Plot(types.ModuleType):
    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


matplotlib = types.ModuleType('matplotlib')
matplotlib.__path__ = []
pyplot = _Plot('matplotlib.pyplot')
matplotlib.pyplot = pyplot
sys.modules['matplotlib'] = matplotlib
sys.modules['matplotlib.pyplot'] = pyplot


def _select_roi(*args, **kwargs):
    roi = CURRENT_PARAMS.get('roi', {'x': 20, 'y': 15, 'w': 360, 'h': 270})
    return tuple(int(roi[key]) for key in ('x', 'y', 'w', 'h'))


cv2.namedWindow = lambda *args, **kwargs: None
cv2.destroyWindow = lambda *args, **kwargs: None
cv2.selectROI = _select_roi


def _source_for(params):
    # These are the notebook's two exposed configuration values, not algorithm code.
    source = SOURCE.replace('K = 3', f"K = {int(params['colorCount'])}", 1)
    source = source.replace('num_aguja = 3', f"num_aguja = {int(params['hookIndex'])}", 1)
    return source


def _execute(code, params, namespace=None):
    global CURRENT_PARAMS
    CURRENT_PARAMS = params
    responses = iter([
        'sí', str(int(params.get('height', 32))), str(int(params.get('width', 32))),
        *['none' if value is None else str(int(value)) for value in params.get('capacities', [])],
    ])
    builtins.input = lambda _prompt='': next(responses)
    namespace = {} if namespace is None else namespace
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(code, 'original_cell.py', 'exec'), namespace)
    return namespace


def _palette(namespace):
    colors = []
    for rgb in namespace['centros_rgb']:
        values = [int(value) for value in rgb]
        colors.append({'rgb': values, 'hex': '#' + ''.join(f'{value:02X}' for value in values)})
    return colors


def run_palette(params_json):
    params = json.loads(params_json)
    namespace = _execute(_source_for(params).split('# 4. CARGAR LA SEGUNDA IMAGEN PARA CUANTIZARLA CON LA PALETA OBTENIDA')[0], params)
    return json.dumps({'palette': _palette(namespace)})


def _english_instructions(source):
    # Only natural-language output is changed. RLE markers and control logic stay intact.
    replacements = [
        ('Hacer una cadeneta de {nuevo_ancho} cadenas.', 'Chain {nuevo_ancho} stitches.'),
        ('Vuelta {nuevo_alto - int(num_fila)}:', 'Row {nuevo_alto - int(num_fila)}:'),
        ('No hay píxeles en esta fila.', 'There are no pixels in this row.'),
        ('Hacer una cadena y {count} punto bajo de color {color}', 'Make a turning chain and {count} single crochet in color {color}'),
        ('Hacer una cadena y {count} puntos bajos de color {color}', 'Make a turning chain and {count} single crochets in color {color}'),
        ('hacer {count} punto bajo de color {color}', 'make {count} single crochet in color {color}'),
        ('hacer {count} puntos bajos de color {color}', 'make {count} single crochets in color {color}'),
        ('Nota: El punto deslizado se realiza en la tercera cadena del bloque de al lado realizado en la vuelta anterior. Sobre esas cadenas es que se realizan los tres puntos altos.', 'Note: Make the slip stitch in the third chain of the adjacent block from the previous row. The three double crochets are worked into those chains.'),
        ('Hacer 6 cadenas y 3 puntos altos desde la cuarta cadena con color {primer_color}', 'Make 6 chains and 3 double crochets starting in the fourth chain with color {primer_color}'),
        ('Hacer 4 puntos deslizados, 3 cadenas y 3 puntos altos con color {primer_color}', 'Make 4 slip stitches, 3 chains and 3 double crochets with color {primer_color}'),
        ('hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}', 'make a slip stitch, 3 chains and 3 double crochets with color {grupos[0][0]}'),
        ('hacer punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}', 'make a slip stitch, 3 chains and 3 double crochets with color {grupos[0][0]}'),
        ('hacer un punto deslizado, 3 cadenas y 3 puntos altos con color {color}', 'make a slip stitch, 3 chains and 3 double crochets with color {color}'),
        ('hacer punto deslizado, 3 cadenas y 3 puntos altos con color {color}', 'make a slip stitch, 3 chains and 3 double crochets with color {color}'),
        ('hacer un punto deslizado, 3 cadenas y 3 puntos altos', 'make a slip stitch, 3 chains and 3 double crochets'),
        ('hacer punto deslizado, 3 cadenas y 3 puntos altos', 'make a slip stitch, 3 chains and 3 double crochets'),
        ('repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {grupos[0][0]}', 'repeat {grupos[0][1]} times the sequence: slip stitch, 3 chains and 3 double crochets with color {grupos[0][0]}'),
        ('repetir {grupos[0][1]} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos', 'repeat {grupos[0][1]} times the sequence: slip stitch, 3 chains and 3 double crochets'),
        ('repetir {rep} veces la secuencia: punto deslizado, 3 cadenas y 3 puntos altos con color {color}', 'repeat {rep} times the sequence: slip stitch, 3 chains and 3 double crochets with color {color}'),
        ('Hacer {primer_bloque} con color {primer_color}', 'Make {primer_bloque} with color {primer_color}'),
        ('partes.append("punto deslizado")', 'partes.append("slip stitch")'),
        ('"4 puntos deslizados, 3 cadenas y 3 puntos altos"', '"4 slip stitches, 3 chains and 3 double crochets"'),
        ('"6 cadenas y 3 puntos altos"', '"6 chains and 3 double crochets"'),
    ]
    for old, new in replacements:
        source = source.replace(old, new)
    return source


def _read(name):
    return Path(name).read_text(encoding='utf-8')


def run_generation(params_json):
    params = json.loads(params_json)
    source = _source_for(params)
    namespace = _execute(source, params)
    spanish = {'rows': _read('instrucciones.txt')}
    spanish['c2c'] = _read('instrucciones_C2C.txt' if namespace['nuevo_alto'] == namespace['nuevo_ancho'] else 'instrucciones_C2C_rect.txt')

    # Reuse the computed labels and rerun only the original instruction/material tail.
    tail_marker = '# 8. IMPRIMIR INSTRUCCIONES (TÉCNICA CON PUNTOS BAJOS: TAPESTRY E INTARSIA)'
    tail = tail_marker + source.split(tail_marker, 1)[1]
    namespace = _execute(_english_instructions(tail), params, namespace)
    english = {'rows': _read('instrucciones.txt')}
    english['c2c'] = _read('instrucciones_C2C.txt' if namespace['nuevo_alto'] == namespace['nuevo_ancho'] else 'instrucciones_C2C_rect.txt')

    ok, encoded = cv2.imencode('.png', cv2.cvtColor(namespace['img2_cuantizada_rgb'], cv2.COLOR_RGB2BGR))
    if not ok:
        raise RuntimeError('Could not encode the quantized pattern')
    pattern_image = 'data:image/png;base64,' + base64.b64encode(encoded.tobytes()).decode('ascii')
    result = {
        'patternImage': pattern_image,
        'labels': (namespace['etiquetas_redim'] + 1).astype(int).tolist(),
        'palette': _palette(namespace),
        'pixelCounts': [int(value) for _, value in namespace['pix_por_centro']],
        'instructions': {'es': spanish, 'en': english},
        'meters': {
            'intarsia': [float(value) for value in namespace['ctdad_hilo_intarsia']],
            'tapestry': [float(value) for value in namespace['ctdad_hilo_tapestry']],
            'c2c': [float(value) for value in namespace['ctdad_hilo_c2c']],
        },
        'dimensions': {
            'rows': [round(float(namespace['ancho_imgt']), 2), round(float(namespace['alto_imgt']), 2)],
            'c2c': [round(float(namespace['ancho_imgc']), 2), round(float(namespace['alto_imgc']), 2)],
        },
        'sourceHash': hashlib.sha256(SOURCE.encode('utf-8')).hexdigest(),
    }
    return json.dumps(result)
