export class DrawingCapture {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.clear();
  }

  clear() {
    this.events = [];
    this.active = false;
    this.interrupted = false;
    this.strokeCount = 0;
  }

  start(point) {
    if (this.active) return;
    this.active = true;
    this.strokeCount += 1;
    this.events.push({ type: 'down', ...point });
  }

  move(point) {
    if (this.active) this.events.push({ type: 'move', ...point });
  }

  end(point) {
    if (!this.active) return;
    this.events.push({ type: 'up', ...point });
    this.active = false;
  }

  cancel(point) {
    if (!this.active) return;
    this.events.push({ type: 'cancel', ...point });
    this.active = false;
    this.interrupted = true;
  }

  sample(target, image) {
    if (!target.trim()) throw new Error('Enter the target character or label.');
    if (!this.events.length) throw new Error('Draw a sample first.');
    if (this.active) throw new Error('Finish the current stroke first.');
    if (this.interrupted) throw new Error('The drawing was interrupted. Clear it and try again.');
    return {
      version: 1,
      createdAt: new Date().toISOString(),
      target: target.trim(),
      canvas: { width: this.width, height: this.height },
      image,
      events: this.events.map(event => ({ ...event })),
    };
  }
}
