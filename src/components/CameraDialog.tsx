import { useEffect, useRef, useState } from 'react';
import { Camera, X } from 'lucide-react';
import type { Copy } from '../i18n';

export function CameraDialog({ t, onCapture, onClose }: { t: Copy; onCapture: (blob: Blob) => void; onClose: () => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const closeRef = useRef(onClose);
  useEffect(() => { closeRef.current = onClose; }, [onClose]);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
      .then((value) => {
        if (!active) { value.getTracks().forEach((track) => track.stop()); return; }
        stream.current = value;
        if (video.current) video.current.srcObject = value;
      })
      .catch(() => setError(true));
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') closeRef.current(); };
    window.addEventListener('keydown', onKey);
    return () => {
      active = false;
      stream.current?.getTracks().forEach((track) => track.stop());
      window.removeEventListener('keydown', onKey);
    };
  }, []);

  function capture() {
    const source = video.current;
    if (!source?.videoWidth) return;
    const canvas = document.createElement('canvas');
    canvas.width = source.videoWidth;
    canvas.height = source.videoHeight;
    canvas.getContext('2d')?.drawImage(source, 0, 0);
    canvas.toBlob((blob) => { if (blob) onCapture(blob); }, 'image/jpeg', 0.9);
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="camera-dialog" role="dialog" aria-modal="true" aria-label={t.captureTitle}>
      <div className="dialog-head"><h2>{t.captureTitle}</h2><button className="icon-button" onClick={onClose} aria-label={t.close}><X /></button></div>
      {error ? <p className="error-message">{t.cameraError}</p> : <video ref={video} autoPlay playsInline muted />}
      <button className="primary-button" onClick={capture} disabled={error}><Camera size={20} />{t.capture}</button>
    </section>
  </div>;
}
