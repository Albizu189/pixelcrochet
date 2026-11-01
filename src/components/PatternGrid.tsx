import type { YarnColor } from '../types';

export function PatternGrid({ labels, palette, activeRow, label }: { labels: number[][]; palette: YarnColor[]; activeRow?: number; label: string }) {
  const width = labels[0]?.length || 1;
  return <div className="pattern-grid" role="img" aria-label={label} style={{ gridTemplateColumns: `repeat(${width}, 1fr)`, aspectRatio: `${width} / ${labels.length}` }}>
    {labels.flatMap((row, rowIndex) => row.map((color, columnIndex) => <span
      key={`${rowIndex}-${columnIndex}`}
      className={activeRow !== undefined && activeRow !== rowIndex ? 'pattern-dimmed' : ''}
      style={{ backgroundColor: palette[color - 1]?.hex || '#888' }}
      title={`${rowIndex + 1}, ${columnIndex + 1}: ${color}`}
    />))}
  </div>;
}
