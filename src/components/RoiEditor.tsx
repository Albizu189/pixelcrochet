import { useRef, useState } from 'react';
import type { Roi } from '../types';

export function RoiEditor({ image, roi, onChange }: { image: string; roi: Roi; onChange: (roi: Roi) => void }) {
  const surface = useRef<HTMLDivElement>(null);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);

  function point(event: React.PointerEvent) {
    const rect = surface.current!.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(400, (event.clientX - rect.left) * 400 / rect.width)),
      y: Math.max(0, Math.min(300, (event.clientY - rect.top) * 300 / rect.height)),
    };
  }
  function down(event: React.PointerEvent) {
    event.currentTarget.setPointerCapture(event.pointerId);
    const p = point(event);
    setStart(p);
    onChange({ x: p.x, y: p.y, w: 1, h: 1 });
  }
  function move(event: React.PointerEvent) {
    if (!start) return;
    const p = point(event);
    onChange({
      x: Math.round(Math.min(start.x, p.x)), y: Math.round(Math.min(start.y, p.y)),
      w: Math.max(1, Math.round(Math.abs(p.x - start.x))), h: Math.max(1, Math.round(Math.abs(p.y - start.y))),
    });
  }

  return <div className="roi-editor" ref={surface} onPointerDown={down} onPointerMove={move} onPointerUp={() => setStart(null)} onPointerCancel={() => setStart(null)}>
    <img src={image} alt="" draggable={false} />
    <div className="roi-shade" />
    <div className="roi-rectangle" style={{ left: `${roi.x / 4}%`, top: `${roi.y / 3}%`, width: `${roi.w / 4}%`, height: `${roi.h / 3}%` }}>
      <span>{Math.round(roi.w)} × {Math.round(roi.h)}</span>
    </div>
  </div>;
}
