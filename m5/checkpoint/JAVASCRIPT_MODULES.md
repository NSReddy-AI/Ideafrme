# JavaScript module inventory
No modules rewritten. Export names/signatures below are extracted from actual .mjs source. No package installation needed for pure helpers. React suitability does not mean a React frontend exists.

## poster_render/backend.mjs
- Exports: none.
- Imports: import fs from 'node:fs/promises';; import path from 'node:path';; import {performance} from 'node:perf_hooks';; import {createRequire} from 'node:module';.
- Not currently suitable for frontend import. Node fs/path/perf_hooks/createRequire and top-level argv/cwd/env validation, file reads, global HyperFrames dependency resolution, subprocess browser launch or native Sharp and output writes. Exports none. Hard-coded original workspace and mandatory Seatbelt runner flag; legacy external-tool adapter.

## tools/r1_canonical.mjs
- Exports: none.
- Imports: import { readFileSync } from 'node:fs';; import { createHash } from 'node:crypto';.
- Not currently suitable for frontend import. R1 CLI canonicalization verifier; Node stdin/fs/process, top-level execution. Included unchanged as accepted source; no R1 refactor or execution in this checkpoint.

## visual_poster_studio/brands.mjs
- Exports: `installBrands(api)`.
- Imports: none declared.
- Reusable through an adapter. No Node dependency; import has no installer side effect, but invoking installer requires existing exact DOM IDs, window/document, event listeners, callbacks and API transport. React needs lifecycle cleanup and state/DOM separation; not drop-in.

## visual_poster_studio/canvas.mjs
- Exports: `selectionBounds(elements,ids)`; `toggleSelection(ids,identity)`; `snappedMove(element,dx,dy,view,options=`; `sameGesture(snapshot,current)`; `installDrag(image,api)`.
- Imports: import {targetsFor,translate} from './geometry.mjs';; import {sourcePoint,hitLayers} from './layout.mjs';.
- Reusable through an adapter (module); pure named helpers directly reusable. Pure geometry helpers run in Node/browser. installDrag/installResize bind pointer, window blur and document key listeners to existing elements; React must own cleanup and controlled state. Do not invoke installers on SSR.

## visual_poster_studio/director.mjs
- Exports: `installDirector(api)`.
- Imports: none declared.
- Reusable through an adapter. No Node dependency; import has no installer side effect, but invoking installer requires existing exact DOM IDs, window/document, event listeners, callbacks and API transport. React needs lifecycle cleanup and state/DOM separation; not drop-in.

## visual_poster_studio/editing.mjs
- Exports: `compositionActive(event,field)`; `shortcut(event,field,editable=false)`; `textStats(text)`; `nextLayerIndex(index,key,count)`; `zoomWidth(value)`; `dialogStillCurrent(snapshot,project,selected)`; `nudge(event,field,editable=false)`.
- Imports: none declared.
- Directly reusable pure helpers. No top-level I/O/DOM access; functions use plain data or supplied event/measurement callbacks. text_layout requires browser font/measurement adapter for real layout; helpers alone do not establish shaping. ES2022 features such as Array.at require a modern engine.

## visual_poster_studio/geometry.mjs
- Exports: `targetsFor(elements,ids)`; `translate(targets,dx,dy)`; `resizeBox(box,corner,dx,dy,locked,view)`; `installResize(image,handles,api)`.
- Imports: none declared.
- Reusable through an adapter (module); pure named helpers directly reusable. Pure geometry helpers run in Node/browser. installDrag/installResize bind pointer, window blur and document key listeners to existing elements; React must own cleanup and controlled state. Do not invoke installers on SSR.

## visual_poster_studio/home.mjs
- Exports: `installHome(api)`.
- Imports: none declared.
- Reusable through an adapter. No Node dependency; import has no installer side effect, but invoking installer requires existing exact DOM IDs, window/document, event listeners, callbacks and API transport. React needs lifecycle cleanup and state/DOM separation; not drop-in.

## visual_poster_studio/layout.mjs
- Exports: `sourcePoint(clientX,clientY,rect,view)`; `hitLayers(elements,point)`; `nextHit(hits,selected,cycle)`; `clippedBox(e,view)`; `alignPosition(e,view,kind,margin=32)`; `shellQuote(value)`.
- Imports: none declared.
- Directly reusable pure helpers. No top-level I/O/DOM access; functions use plain data or supplied event/measurement callbacks. text_layout requires browser font/measurement adapter for real layout; helpers alone do not establish shaping. ES2022 features such as Array.at require a modern engine.

## visual_poster_studio/text_layout.mjs
- Exports: `wrapText(text,width,measure)`; `fitTextBox(text,size,measure,descent=0)`; `keyboardGeometry(event,composing,editable)`; `fontRuns(text)`.
- Imports: none declared.
- Directly reusable pure helpers. No top-level I/O/DOM access; functions use plain data or supplied event/measurement callbacks. text_layout requires browser font/measurement adapter for real layout; helpers alone do not establish shaping. ES2022 features such as Array.at require a modern engine.

## visual_poster_tests/canvas_browser.mjs
- Exports: none.
- Imports: none declared.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/editing_browser.mjs
- Exports: none.
- Imports: none declared.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/geometry_browser.mjs
- Exports: none.
- Imports: none declared.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/layout_browser.mjs
- Exports: none.
- Imports: none declared.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/test_canvas.mjs
- Exports: none.
- Imports: import assert from 'node:assert/strict';; import {selectionBounds,toggleSelection,snappedMove,sameGesture,installDrag} from '../visual_poster_studio/canvas.mjs';.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/test_editing.mjs
- Exports: none.
- Imports: import assert from 'node:assert/strict';; import {compositionActive,shortcut,textStats,nextLayerIndex,zoomWidth} from '../visual_poster_studio/editing.mjs';; import {dialogStillCurrent,nudge} from '../visual_poster_studio/editing.mjs';.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/test_geometry.mjs
- Exports: none.
- Imports: import assert from 'node:assert/strict';; import {targetsFor,translate,resizeBox} from '../visual_poster_studio/geometry.mjs';.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/test_layout.mjs
- Exports: none.
- Imports: import assert from 'node:assert/strict';; import {sourcePoint,hitLayers,nextHit,clippedBox,alignPosition,shellQuote} from '../visual_poster_studio/layout.mjs';.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/test_text_layout.mjs
- Exports: none.
- Imports: import assert from 'node:assert/strict';; import {wrapText,fitTextBox,keyboardGeometry,fontRuns} from '../visual_poster_studio/text_layout.mjs';.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

## visual_poster_tests/text_completion_browser.mjs
- Exports: none.
- Imports: none declared.
- Not currently suitable as a frontend application module. Test/acceptance harness; top-level assertions or browser QA actions. Node tests use node:assert, browser harnesses use DOM and local API and may write evidence through service. Reuse test ideas rather than import into product.

