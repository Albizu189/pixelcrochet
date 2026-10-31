# PixelCrochet

Aplicación móvil instalable y offline que convierte una imagen en un patrón plano de crochet usando los colores detectados en una fotografía de las lanas. Genera instrucciones en español e inglés, estima los metros por color y guarda el avance de cada proyecto en el dispositivo.

Basada en la tesis **«Cuantización del color como paso intermedio para la obtención automática de patrones de Crochet»**, de **Erika Torres Figueiras** (Universidad de La Habana, 2026).

## Funciones

- Cámara del dispositivo o galería para las dos imágenes.
- Selección visual del área de lanas y paleta mediante GrabCut + k-means.
- Capacidades máximas por color, dimensiones, técnica y aguja configurables.
- Tapestry, intarsia y corner-to-corner (C2C).
- Patrón pixelado, instrucciones ES/EN y materiales estimados.
- Seguimiento paso a paso con fecha del último paso completado.
- Proyectos y borradores: crear, modificar, continuar y eliminar.
- Guardado automático en IndexedDB, incluso al navegar o cerrar.
- Tema claro/oscuro y aplicación adaptable a móvil y escritorio.
- Funcionamiento offline después de la primera carga completa.

## Primera build

Requisitos: **Node.js 20+**, **npm** y **Python 3.10+**. No hace falta instalar las dependencias científicas de Python en el ordenador: el build descarga sus versiones WebAssembly.

```bash
git clone https://github.com/Albizu189/pixelcrochet.git
cd pixelcrochet
npm install
npm run build
npm run preview
```

Abre la dirección que muestra `npm run preview`. `npm run build` ejecuta automáticamente `scripts/setup_pyodide.py`, que deja en `public/pyodide/` el runtime y los paquetes necesarios. Estos archivos binarios no se versionan; se descargan durante la primera build.

Para desarrollo:

```bash
python3 scripts/setup_pyodide.py
npm run dev
```

La cámara requiere HTTPS o `localhost` y permiso del navegador. Para instalar la app en el teléfono, sirve la build mediante HTTPS y elige **Añadir a pantalla de inicio / Instalar app**. La primera carga debe completarse con conexión para que el service worker almacene el motor offline.

## Prueba del algoritmo original

Para ejecutar la prueba local con CPython sí se necesitan `opencv-python`, `numpy`, `scipy` y `scikit-learn`:

```bash
pip install opencv-python numpy scipy scikit-learn
npm test
```

La prueba genera imágenes sintéticas y comprueba paleta, heurística con capacidades, patrón, instrucciones en ambos idiomas, C2C y materiales.

## Código original y adaptación

- `public/algorithms/original_cell.py`: contenido exacto de la celda principal del notebook entregado, sin modificaciones.
- `public/algorithms/runner.py`: adaptador de entrada/salida. Solo cambia los parámetros expuestos (`K`, `num_aguja`), sustituye las respuestas de `input()` y `selectROI()`, desactiva las ventanas/gráficos y traduce los textos naturales de las instrucciones. No reescribe los algoritmos.
- `public/workers/crochet-worker.js`: ejecuta ese código en Pyodide. Cancelar termina el worker y conserva el borrador.

## Datos y privacidad

No hay backend, cuentas ni analítica. Fotos, borradores, proyectos y avance se guardan únicamente en IndexedDB en el navegador/dispositivo. No se sincronizan entre dispositivos; borrar los datos del navegador también borra esta información.

## Estructura

```text
src/                    interfaz React + TypeScript
public/algorithms/      código original y adaptador Python
public/workers/         motor de cálculo cancelable
public/pyodide/         runtime offline generado en la build
scripts/                preparación y pruebas
```

## Colaborar

Las propuestas son bienvenidas mediante issues y pull requests. Por favor, conserva intactos los algoritmos de `original_cell.py`; cualquier cambio científico debe discutirse y validarse contra el notebook original.
