export function imagePreviewSource(sample) {
  return typeof sample?.image === 'string' && sample.image.startsWith('data:image/png;base64,') ? sample.image : null;
}

export function provisionalMeasurements(branch) {
  if (!Array.isArray(branch?.evidence)) return null;
  const item = branch?.evidence?.find(evidence => evidence?.code === 'provisional_measurements');
  return item?.measurements || null;
}
