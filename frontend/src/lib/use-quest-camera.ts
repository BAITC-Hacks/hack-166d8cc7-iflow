'use client';

import { useCallback, useEffect, useRef, useState, type HTMLAttributes, type RefObject } from 'react';

export interface Point { x: number; y: number }
export interface QuestCamera extends Point { zoom: number }

interface Options {
  worldWidth: number;
  worldHeight: number;
  initialFocus: Point;
  enabled: boolean;
}

interface CameraControls {
  viewportRef: RefObject<HTMLDivElement | null>;
  camera: QuestCamera;
  viewport: { width: number; height: number };
  dragging: boolean;
  viewportProps: HTMLAttributes<HTMLDivElement>;
  pan(dx: number, dy: number): void;
  zoomBy(factor: number): void;
  focusAt(point: Point): void;
  reset(): void;
}

type TrackedPointer = Point & { startX: number; startY: number };

const MIN_ZOOM = 0.45;
const MAX_ZOOM = 1.5;
const DEFAULT_ZOOM = 0.85;
const DRAG_THRESHOLD = 6;
const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

/** Camera coordinates are screen pixels; node coordinates stay in world pixels. */
export function useQuestCamera({ worldWidth, worldHeight, initialFocus, enabled }: Options): CameraControls {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [camera, setCamera] = useState<QuestCamera>({ x: 0, y: 0, zoom: DEFAULT_ZOOM });
  const [viewport, setViewport] = useState({ width: 0, height: 0 });
  const [dragging, setDragging] = useState(false);
  const cameraRef = useRef(camera);
  const sizeRef = useRef(viewport);
  const initialFocusRef = useRef(initialFocus);
  const pointers = useRef(new Map<number, TrackedPointer>());
  const dragActive = useRef(false);
  const suppressClickUntil = useRef(0);
  initialFocusRef.current = initialFocus;

  const finishPointer = useCallback((pointerId: number) => {
    if (!pointers.current.has(pointerId)) return;
    pointers.current.delete(pointerId);
    const element = viewportRef.current;
    if (element?.hasPointerCapture(pointerId)) element.releasePointerCapture(pointerId);
    if (dragActive.current) suppressClickUntil.current = performance.now() + 350;
    if (!pointers.current.size) {
      dragActive.current = false;
      setDragging(false);
    } else {
      for (const point of pointers.current.values()) { point.startX = point.x; point.startY = point.y; }
    }
  }, []);

  const clearPointers = useCallback(() => {
    for (const pointerId of Array.from(pointers.current.keys())) finishPointer(pointerId);
  }, [finishPointer]);

  const clearScrollOffsets = useCallback(() => {
    // Hidden overflow can be scrolled by native Tab focus. Camera transforms own this position.
    const element = viewportRef.current;
    if (!element) return;
    if (element.scrollLeft) element.scrollLeft = 0;
    if (element.scrollTop) element.scrollTop = 0;
  }, []);

  const applyCamera = useCallback((next: QuestCamera) => {
    const size = sizeRef.current;
    const zoom = clamp(next.zoom, MIN_ZOOM, MAX_ZOOM);
    const scaledWidth = worldWidth * zoom;
    const scaledHeight = worldHeight * zoom;
    const bounded = {
      zoom,
      x: scaledWidth <= size.width ? (size.width - scaledWidth) / 2 : clamp(next.x, size.width - scaledWidth, 0),
      y: scaledHeight <= size.height ? (size.height - scaledHeight) / 2 : clamp(next.y, size.height - scaledHeight, 0),
    };
    clearScrollOffsets();
    const previous = cameraRef.current;
    if (previous.x === bounded.x && previous.y === bounded.y && previous.zoom === bounded.zoom) return;
    cameraRef.current = bounded;
    setCamera(bounded);
  }, [worldWidth, worldHeight, clearScrollOffsets]);

  const pan = useCallback((dx: number, dy: number) => {
    const current = cameraRef.current;
    applyCamera({ ...current, x: current.x + dx, y: current.y + dy });
  }, [applyCamera]);

  const zoomAt = useCallback((factor: number, anchor: Point) => {
    if (!Number.isFinite(factor) || factor <= 0) return;
    const current = cameraRef.current;
    const zoom = clamp(current.zoom * factor, MIN_ZOOM, MAX_ZOOM);
    const ratio = zoom / current.zoom;
    applyCamera({ x: anchor.x - (anchor.x - current.x) * ratio, y: anchor.y - (anchor.y - current.y) * ratio, zoom });
  }, [applyCamera]);

  const zoomBy = useCallback((factor: number) => {
    const size = sizeRef.current;
    zoomAt(factor, { x: size.width / 2, y: size.height / 2 });
  }, [zoomAt]);

  const focusAt = useCallback((point: Point) => {
    const zoom = cameraRef.current.zoom;
    const size = sizeRef.current;
    applyCamera({ x: size.width / 2 - point.x * zoom, y: size.height / 2 - point.y * zoom, zoom });
  }, [applyCamera]);

  const reset = useCallback(() => {
    const point = initialFocusRef.current;
    const size = sizeRef.current;
    applyCamera({ x: size.width / 2 - point.x * DEFAULT_ZOOM, y: size.height / 2 - point.y * DEFAULT_ZOOM, zoom: DEFAULT_ZOOM });
  }, [applyCamera]);

  useEffect(() => {
    const element = viewportRef.current;
    if (!enabled || !element) return;
    let firstMeasurement = true;
    const measure = () => {
      const nextSize = { width: element.clientWidth, height: element.clientHeight };
      if (!nextSize.width || !nextSize.height) return;
      const oldSize = sizeRef.current;
      const current = cameraRef.current;
      sizeRef.current = nextSize;
      setViewport(previous => previous.width === nextSize.width && previous.height === nextSize.height ? previous : nextSize);
      if (firstMeasurement) {
        firstMeasurement = false;
        focusAt(initialFocusRef.current);
      } else {
        // Preserve the point at the center when the surrounding layout changes.
        applyCamera({ ...current, x: current.x + (nextSize.width - oldSize.width) / 2, y: current.y + (nextSize.height - oldSize.height) / 2 });
      }
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [enabled, applyCamera, focusAt]);

  useEffect(() => {
    if (enabled && sizeRef.current.width) focusAt({ x: initialFocus.x, y: initialFocus.y });
  }, [enabled, initialFocus.x, initialFocus.y, focusAt]);

  useEffect(() => {
    const element = viewportRef.current;
    if (!enabled || !element) return;
    // Pointer up may occur outside the viewport before the drag threshold acquired capture.
    const handlePointerEnd = (event: PointerEvent) => finishPointer(event.pointerId);
    const handleVisibility = () => { if (document.hidden) clearPointers(); };
    const handleWheel = (event: WheelEvent) => {
      if ((event.target as Element).closest('[data-camera-control]')) return;
      event.preventDefault();
      const unit = event.deltaMode === 1 ? 18 : event.deltaMode === 2 ? element.clientHeight : 1;
      if (event.ctrlKey || event.metaKey) {
        const rect = element.getBoundingClientRect();
        zoomAt(Math.exp(-event.deltaY * unit * 0.006), { x: event.clientX - rect.left, y: event.clientY - rect.top });
      } else {
        const dx = event.shiftKey && !event.deltaX ? event.deltaY : event.deltaX;
        const dy = event.shiftKey && !event.deltaX ? 0 : event.deltaY;
        pan(-dx * unit, -dy * unit);
      }
    };
    element.addEventListener('wheel', handleWheel, { passive: false });
    window.addEventListener('pointerup', handlePointerEnd);
    window.addEventListener('pointercancel', handlePointerEnd);
    window.addEventListener('blur', clearPointers);
    document.addEventListener('visibilitychange', handleVisibility);
    return () => {
      element.removeEventListener('wheel', handleWheel);
      window.removeEventListener('pointerup', handlePointerEnd);
      window.removeEventListener('pointercancel', handlePointerEnd);
      window.removeEventListener('blur', clearPointers);
      document.removeEventListener('visibilitychange', handleVisibility);
      clearPointers();
    };
  }, [enabled, pan, zoomAt, finishPointer, clearPointers]);

  const viewportProps: HTMLAttributes<HTMLDivElement> = {
    tabIndex: 0,
    onPointerDown(event) {
      if (!enabled || (event.pointerType === 'mouse' && event.button !== 0)) return;
      const target = event.target as Element;
      if (target.closest('input, textarea, select, [contenteditable="true"], [data-camera-control]')) return;
      if (event.pointerType === 'mouse') clearPointers();
      suppressClickUntil.current = 0;
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY });
      if (!target.closest('button, a')) event.currentTarget.focus({ preventScroll: true });
      // Delay capture until movement; capturing here would redirect ordinary button clicks.
      if (pointers.current.size > 1) {
        dragActive.current = true;
        setDragging(true);
        event.currentTarget.focus({ preventScroll: true });
        for (const id of pointers.current.keys()) event.currentTarget.setPointerCapture(id);
        event.preventDefault();
      }
    },
    onPointerMove(event) {
      const point = pointers.current.get(event.pointerId);
      if (!enabled || !point) return;
      if (event.pointerType === 'mouse' && event.buttons === 0) { finishPointer(event.pointerId); return; }
      const previousPoints = Array.from(pointers.current.values()).slice(0, 2).map(value => ({ x: value.x, y: value.y }));
      const oldX = point.x;
      const oldY = point.y;
      point.x = event.clientX;
      point.y = event.clientY;
      if (pointers.current.size > 1) {
        const nextPoints = Array.from(pointers.current.values()).slice(0, 2);
        const previousDistance = Math.hypot(previousPoints[0].x - previousPoints[1].x, previousPoints[0].y - previousPoints[1].y);
        const nextDistance = Math.hypot(nextPoints[0].x - nextPoints[1].x, nextPoints[0].y - nextPoints[1].y);
        const rect = event.currentTarget.getBoundingClientRect();
        const previousCenter = { x: (previousPoints[0].x + previousPoints[1].x) / 2 - rect.left, y: (previousPoints[0].y + previousPoints[1].y) / 2 - rect.top };
        const nextCenter = { x: (nextPoints[0].x + nextPoints[1].x) / 2 - rect.left, y: (nextPoints[0].y + nextPoints[1].y) / 2 - rect.top };
        const current = cameraRef.current;
        const zoom = clamp(current.zoom * (previousDistance > 1 ? nextDistance / previousDistance : 1), MIN_ZOOM, MAX_ZOOM);
        applyCamera({ x: nextCenter.x - (previousCenter.x - current.x) * zoom / current.zoom, y: nextCenter.y - (previousCenter.y - current.y) * zoom / current.zoom, zoom });
        event.preventDefault();
        return;
      }
      if (!dragActive.current) {
        if (Math.hypot(point.x - point.startX, point.y - point.startY) < DRAG_THRESHOLD) return;
        dragActive.current = true;
        setDragging(true);
        event.currentTarget.setPointerCapture(event.pointerId);
        event.currentTarget.focus({ preventScroll: true });
        pan(point.x - point.startX, point.y - point.startY);
      } else {
        pan(point.x - oldX, point.y - oldY);
      }
      event.preventDefault();
    },
    onPointerUp: event => finishPointer(event.pointerId),
    onPointerCancel: event => finishPointer(event.pointerId),
    onPointerLeave(event) {
      if (event.pointerType === 'mouse' && !event.currentTarget.hasPointerCapture(event.pointerId)) finishPointer(event.pointerId);
    },
    onLostPointerCapture(event) {
      // A child's implicit touch capture may be transferred to the viewport during a drag.
      if (!event.currentTarget.hasPointerCapture(event.pointerId)) finishPointer(event.pointerId);
    },
    onClickCapture(event) {
      if (event.detail !== 0 && performance.now() < suppressClickUntil.current) {
        event.preventDefault();
        event.stopPropagation();
      }
    },
    onFocusCapture: clearScrollOffsets,
    onScroll: clearScrollOffsets,
    onKeyDown(event) {
      if (!enabled || event.target !== event.currentTarget || event.ctrlKey || event.metaKey || event.altKey) return;
      const distance = event.shiftKey ? 180 : 90;
      switch (event.key.toLowerCase()) {
        case 'arrowleft': case 'a': pan(distance, 0); break;
        case 'arrowright': case 'd': pan(-distance, 0); break;
        case 'arrowup': case 'w': pan(0, distance); break;
        case 'arrowdown': case 's': pan(0, -distance); break;
        case '+': case '=': zoomBy(1.15); break;
        case '-': case '_': zoomBy(1 / 1.15); break;
        case '0': reset(); break;
        default: return;
      }
      event.preventDefault();
    },
  };

  return { viewportRef, camera, viewport, dragging, viewportProps, pan, zoomBy, focusAt, reset };
}
