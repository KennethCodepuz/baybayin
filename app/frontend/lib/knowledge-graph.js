export function catalogTargets(catalog) {
  if (!catalog || !Array.isArray(catalog.targets)) return [];
  return catalog.targets.filter(target =>
    target && typeof target.id === 'string' && typeof target.targetId === 'string'
      && Array.isArray(target.sourceRefs) && target.scoringAvailable === false,
  );
}

export function selectedTarget(catalog, targetId) {
  return catalogTargets(catalog).find(target => target.targetId === targetId) || null;
}