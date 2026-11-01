/* Runs the original thesis Python in a cancellable worker. */
let pyodide = null;
let ready = null;

function bytesFromDataUrl(dataUrl) {
  const base64 = dataUrl.split(',')[1];
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function initialize() {
  if (ready) return ready;
  ready = (async () => {
    postMessage({ type: 'status', stage: 'runtime' });
    importScripts('/pyodide/pyodide.js');
    pyodide = await loadPyodide({ indexURL: `${self.location.origin}/pyodide/` });
    await pyodide.loadPackage(['numpy', 'scipy', 'scikit-learn', 'opencv-python']);
    const [original, runner] = await Promise.all([
      fetch('/algorithms/original_cell.py').then((r) => r.text()),
      fetch('/algorithms/runner.py').then((r) => r.text()),
    ]);
    pyodide.FS.writeFile('/home/pyodide/original_cell.py', original);
    await pyodide.runPythonAsync(runner);
  })();
  return ready;
}

self.onmessage = async (event) => {
  const { type, params } = event.data;
  if (type !== 'palette' && type !== 'generate') return;
  try {
    await initialize();
    if (params.yarnImage) pyodide.FS.writeFile('/home/pyodide/hilo3.jpg', bytesFromDataUrl(params.yarnImage));
    if (params.patternImage) pyodide.FS.writeFile('/home/pyodide/ardillaoops.jpg', bytesFromDataUrl(params.patternImage));
    pyodide.globals.set('app_params_json', JSON.stringify(params));
    postMessage({ type: 'status', stage: type === 'palette' ? 'palette' : 'quantize' });
    const fn = type === 'palette' ? 'run_palette' : 'run_generation';
    const result = await pyodide.runPythonAsync(`app_result_json = ${fn}(app_params_json)\napp_result_json`);
    postMessage({ type: 'result', operation: type, result: JSON.parse(result) });
  } catch (error) {
    postMessage({ type: 'error', message: error?.message || String(error) });
  }
};
