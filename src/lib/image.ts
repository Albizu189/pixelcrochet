export async function imageFileToDataUrl(file: File | Blob): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 1400 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Canvas is unavailable');
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas.toDataURL('image/jpeg', 0.88);
}

export function stepsFromInstructions(text: string, technique: 'rows' | 'c2c') {
  const chunks = technique === 'rows'
    ? text.split(/\n\s*\n/).map((part) => part.trim()).filter(Boolean)
    : text.split('\n').map((part) => part.trim()).filter(Boolean);
  return chunks.map((chunk, index) => ({
    text: chunk,
    label: chunk.match(/^(Vuelta|Row|Diagonal)\s+\d+/i)?.[0] || String(index + 1),
    colorIndexes: [...chunk.matchAll(/(?:color|colour)\s+(\d+)/gi)].map((match) => Number(match[1])),
  }));
}
