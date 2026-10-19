export const MAX_IMPORT_BYTES = 32 * 1024 * 1024;
const MAX_DIMENSION = 1_000_000;
const apiUrl = 'http://127.0.0.1:8000/api/samples/check';

export async function loadRecording(file, request = fetch) {
  if (file.size > MAX_IMPORT_BYTES) throw new Error('This file is too large. Choose a JSON file of 32 MiB or less.');
  let sample;
  try {
    sample = JSON.parse(await file.text());
  } catch {
    throw new Error('Could not read this file as JSON. Choose a saved drawing sample.');
  }
  if (!sample || typeof sample !== 'object' || Array.isArray(sample)) {
    throw new Error('This JSON is not a drawing sample.');
  }
  if (sample.version !== 1) throw new Error('This sample version is not supported. Choose a version 1 sample.');
  const { width, height } = sample.canvas || {};
  if (![width, height].every(value => Number.isInteger(value) && value > 0 && value <= MAX_DIMENSION)) {
    throw new Error('The sample canvas dimensions are missing or unsupported.');
  }
  let response;
  try {
    response = await request(apiUrl, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sample),
    });
  } catch {
    throw new Error('Cannot reach the backend. Make sure FastAPI is running on port 8000.');
  }
  if (!response.ok) {
    if (response.status === 422) throw new Error('This sample is invalid or incomplete. Check its fields and stroke events.');
    throw new Error('The backend could not check this sample. Please try again.');
  }
  return sample;
}

export function fitRecording(sourceWidth, sourceHeight, displayWidth, displayHeight) {
  const scale = Math.min(displayWidth / sourceWidth, displayHeight / sourceHeight);
  return { scale, x: (displayWidth - sourceWidth * scale) / 2, y: (displayHeight - sourceHeight * scale) / 2 };
}

export function eventsDue(events, startIndex, elapsed) {
  let index = startIndex;
  while (index < events.length && events[index].timestamp - events[0].timestamp <= elapsed) index++;
  return index;
}

export function drawRecordingEvent(ctx, event) {
  if (event.type === 'down') {
    ctx.beginPath();
    ctx.arc(event.x, event.y, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(event.x, event.y);
  } else if (event.type === 'move' || event.type === 'up') {
    ctx.lineTo(event.x, event.y);
    ctx.stroke();
  }
}
