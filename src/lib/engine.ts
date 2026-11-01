import type { GenerationResult, YarnColor } from '../types';

export type EngineStage = 'runtime' | 'palette' | 'quantize';

export function runEngine(
  operation: 'palette' | 'generate',
  params: Record<string, unknown>,
  onStatus: (stage: EngineStage) => void,
) {
  const worker = new Worker('/workers/crochet-worker.js');
  let settled = false;
  const promise = new Promise<{ palette?: YarnColor[] } & GenerationResult>((resolve, reject) => {
    worker.onmessage = (event) => {
      const message = event.data;
      if (message.type === 'status') onStatus(message.stage);
      if (message.type === 'result') {
        settled = true;
        resolve(message.result);
        worker.terminate();
      }
      if (message.type === 'error') {
        settled = true;
        reject(new Error(message.message));
        worker.terminate();
      }
    };
    worker.onerror = (event) => {
      if (!settled) reject(new Error(event.message));
      worker.terminate();
    };
    void (async () => {
      try {
        if ('serviceWorker' in navigator) {
          const registration = await navigator.serviceWorker.getRegistration();
          if (registration && !registration.active) {
            // Avoid downloading the scientific packages twice while offline support is installing.
            await Promise.race([
              navigator.serviceWorker.ready,
              new Promise<void>((resolve) => window.setTimeout(resolve, 180000)),
            ]);
          }
        }
      } catch {
        // Offline preparation is optional; the engine can still run online.
      }
      if (!settled) worker.postMessage({ type: operation, params });
    })();
  });
  return {
    promise,
    cancel() {
      settled = true;
      worker.terminate();
    },
  };
}
