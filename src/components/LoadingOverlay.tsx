import { X } from 'lucide-react';
import type { Copy } from '../i18n';
import type { EngineStage } from '../lib/engine';

export function LoadingOverlay({ t, stage, onCancel }: { t: Copy; stage: EngineStage; onCancel: () => void }) {
  const text = stage === 'runtime' ? t.loadingRuntime : stage === 'palette' ? t.loadingPalette : t.loadingQuantize;
  return <div className="loading-overlay" role="dialog" aria-modal="true" aria-live="polite" aria-label={t.loadingTitle}>
    <div className="loading-content">
      <div className="yarn-loader" aria-hidden="true"><span /><span /><span /><i /></div>
      <h2>{t.loadingTitle}</h2>
      <p>{t.loadingText}</p>
      <div className="loading-status"><span className="status-dot" />{text}</div>
      <button className="secondary-button" onClick={onCancel}><X size={19} />{t.cancelOperation}</button>
    </div>
  </div>;
}
