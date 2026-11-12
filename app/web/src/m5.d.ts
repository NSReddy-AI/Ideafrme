// Types for the M5 modules the React editor imports unchanged from ../../m5 (alias @m5 in vite.config.ts).
// Signatures follow m5/checkpoint/JAVASCRIPT_MODULES.md; keep them in step with the M5 checkpoint.
declare module '@m5/visual_poster_tests/browser_acceptance.js' {
  type Faces = Record<string, { family: string; weight: number; uri: string }>
  export function loadFonts(faces: Faces): Promise<void>
  export function inspectScene(scene: { svg: string; boxes: { id: string; element_id: string; x: number; y: number; width: number; height: number }[] }): Promise<{ fonts_loaded: boolean; overflow: string[] }>
  export function raster(svg: string): Promise<{ canvas: HTMLCanvasElement; blob: Blob }>
  export function comparePng(canvas: HTMLCanvasElement, blob: Blob): Promise<boolean>
  export function qualifyEmbedded(faces: Faces): Promise<{ ok: boolean; reason: string | null }>
}
declare module '@m5/visual_poster_studio/layout.mjs' {
  type Box = { x: number; y: number; width: number; height: number }
  export function alignPosition(e: Box, view: { width: number; height: number }, kind: 'left' | 'center-x' | 'right' | 'top' | 'center-y' | 'bottom', margin?: number): { x: number; y: number }
  export function clippedBox(e: Box | null, view: { width: number; height: number }): { left: number; top: number; width: number; height: number } | null
}
declare module '@m5/visual_poster_studio/geometry.mjs' {
  type Box = { x: number; y: number; width: number; height: number }
  export function resizeBox(box: Box, corner: 'nw' | 'ne' | 'sw' | 'se', dx: number, dy: number, locked: boolean, view: { width: number; height: number }): Box
}
