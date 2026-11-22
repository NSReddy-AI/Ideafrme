// Shared UI pieces (M7-B slice B1). Colours, radii, shadows and motion come only from design/tokens/tokens.css via the
// short utility names in index.css; never hard-code them here or in a screen (tools/m6_token_audit.py checks this).
// States follow the Design System Bible: default, hover, pressed, focus-visible, loading, disabled, error, success.
import { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import { nextTab, toastLifetime, TONE_LABEL, type Tone } from './ui-logic'

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(' ')
export const MOTION = 'transition duration-[var(--motion-fast)] ease-[var(--ease-out)]'

// ------------------------------------------------------------------ buttons
export function Spinner({ label }: { label?: string }) {
  return <span role={label ? 'status' : undefined} aria-label={label} className="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none" />
}

type BtnKind = 'primary' | 'ghost' | 'danger' | 'quiet'
export function Btn({ kind = 'primary', busy = false, className, children, disabled, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { kind?: BtnKind; busy?: boolean }) {
  return <button {...p} disabled={disabled || busy} aria-busy={busy || undefined}
    className={cx('inline-flex min-h-[var(--control-height)] items-center justify-center gap-1.5 rounded-btn px-[var(--control-padding-x)] text-sm font-semibold',
      MOTION, 'enabled:active:scale-[var(--press-scale)] disabled:cursor-not-allowed', busy ? 'cursor-progress' : 'disabled:opacity-50',
      kind === 'primary' && 'bg-act text-on-act enabled:hover:bg-act-hover enabled:active:bg-act-pressed',
      kind === 'ghost' && 'border border-line-strong bg-raised text-ink enabled:hover:bg-act-subtle',
      kind === 'quiet' && 'text-ink-2 enabled:hover:bg-surface enabled:hover:text-ink',
      kind === 'danger' && 'bg-bad-solid text-on-act enabled:hover:bg-bad-solid-hover', className)}>
    {busy && <Spinner />}{children}
  </button>
}

// ------------------------------------------------------------------ containers and status
export function Card({ title, step, state, children, right }: { title: string; step?: number; state?: 'done' | 'next' | 'todo'; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section className={cx('rounded-box border bg-raised p-6 shadow-soft', state === 'next' ? 'border-act ring-1 ring-act' : 'border-line')}>
      <header className="mb-4 flex flex-wrap items-center gap-3">
        {step !== undefined && <span className={cx('flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold',
          state === 'done' ? 'bg-ok-subtle text-ok' : state === 'next' ? 'bg-act text-on-act' : 'bg-surface text-ink-3')}>{state === 'done' ? '✓' : step}<span className="sr-only">{state === 'done' ? ' done' : state === 'next' ? ' next' : ''}</span></span>}
        <h2 className="text-base font-semibold">{title}</h2>
        <div className="ml-auto">{right}</div>
      </header>
      {children}
    </section>
  )
}

export const Pill = ({ ok, children }: { ok?: boolean | null; children: React.ReactNode }) =>
  <span className={cx('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', ok === true && 'bg-ok-subtle text-ok', ok === false && 'bg-bad-subtle text-bad', ok == null && 'bg-raised text-ink-2 ring-1 ring-inset ring-line')}>{children}</span>

const TONE_STYLE: Record<Tone, string> = { info: 'bg-note-subtle text-note', success: 'bg-ok-subtle text-ok', warning: 'bg-warn-subtle text-warn', error: 'bg-bad-subtle text-bad' }

/** Inline message with a symbol and a word, never colour alone. Errors and warnings are announced immediately. */
export function Notice({ tone = 'info', title, children, className }: { tone?: Tone; title?: string; children?: React.ReactNode; className?: string }) {
  const t = TONE_LABEL[tone]
  return <div role={tone === 'error' || tone === 'warning' ? 'alert' : 'status'} className={cx('flex gap-2 rounded-field px-3 py-2 text-sm', TONE_STYLE[tone], className)}>
    <span aria-hidden className="mt-px font-semibold">{t.symbol}</span>
    <div className="min-w-0"><span className="sr-only">{t.word}: </span>{title && <strong className="font-semibold">{title} </strong>}{children}</div>
  </div>
}

/** The original one-line error, kept for existing screens. */
export const Err = ({ msg }: { msg: string | null }) => msg ? <Notice tone="error" className="mt-2">{msg}</Notice> : null

// ------------------------------------------------------------------ form controls
const CONTROL = 'min-h-9 rounded-field border bg-raised px-2 py-1.5 text-sm text-ink placeholder:text-ink-3 disabled:cursor-not-allowed disabled:bg-surface disabled:text-ink-off'
const edge = (invalid?: boolean) => (invalid ? 'border-bad-solid' : 'border-line-strong')

export const Select = ({ className, invalid, ...p }: React.SelectHTMLAttributes<HTMLSelectElement> & { invalid?: boolean }) =>
  <select {...p} aria-invalid={invalid || undefined} className={cx(CONTROL, 'max-w-full', edge(invalid), className)} />

export const Field = ({ className, invalid, ...p }: React.InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }) =>
  <input {...p} aria-invalid={invalid || undefined} className={cx(CONTROL, 'w-full', edge(invalid), className)} />

export const TextArea = ({ className, invalid, ...p }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }) =>
  <textarea {...p} aria-invalid={invalid || undefined} className={cx(CONTROL, 'w-full p-2', edge(invalid), className)} />

/** Label above, help and error below, all linked to the control for screen readers (Bible: label always visible). */
export function FormRow({ label, help, error, children }: { label: string; help?: string; error?: string | null; children: (a: { id: string; describedBy?: string; invalid: boolean }) => React.ReactNode }) {
  const id = useId(); const helpId = `${id}-help`; const errId = `${id}-error`
  const describedBy = [help ? helpId : null, error ? errId : null].filter(Boolean).join(' ') || undefined
  return <div className="space-y-1">
    <label htmlFor={id} className="block text-xs font-medium text-ink-2">{label}</label>
    {children({ id, describedBy, invalid: !!error })}
    {help && <p id={helpId} className="text-xs text-ink-3">{help}</p>}
    {error && <p id={errId} className="text-xs text-bad"><span aria-hidden>× </span>{error}</p>}
  </div>
}

// ------------------------------------------------------------------ tabs / segmented control
export function Tabs<T extends string>({ label, tabs, value, onChange }: { label: string; tabs: { id: T; label: string }[]; value: T; onChange: (v: T) => void }) {
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const key = (e: React.KeyboardEvent, i: number) => {
    const j = nextTab(i, e.key, tabs.length); if (j === null) return
    e.preventDefault(); onChange(tabs[j].id); refs.current[j]?.focus()
  }
  return <div role="tablist" aria-label={label} className="inline-flex gap-1 rounded-field bg-surface p-1">
    {tabs.map((t, i) => <button key={t.id} ref={el => { refs.current[i] = el }} role="tab" aria-selected={value === t.id} tabIndex={value === t.id ? 0 : -1}
      onClick={() => onChange(t.id)} onKeyDown={e => key(e, i)}
      className={cx('rounded-field px-3 py-1.5 text-sm font-medium', 'transition duration-[var(--motion-base)] ease-[var(--ease-out)]',
        value === t.id ? 'bg-raised text-ink shadow-soft' : 'text-ink-2 hover:text-ink')}>{t.label}</button>)}
  </div>
}

// ------------------------------------------------------------------ page heading
export function PageHead({ title, sub }: { title: string; sub?: string }) {
  return <header className="mb-6"><h1 className="font-head text-[length:var(--text-title)] leading-[var(--leading-title)] font-semibold tracking-[var(--tracking-title)]">{title}</h1>
    {sub && <p className="mt-1 text-sm text-ink-2">{sub}</p>}</header>
}

// ------------------------------------------------------------------ confirmation dialog (native <dialog>: focus trap, Escape, inert page)
type ConfirmOpts = { title: string; body?: React.ReactNode; confirmLabel: string; cancelLabel?: string; tone?: 'danger' | 'primary' }
const ConfirmCtx = createContext<(o: ConfirmOpts) => Promise<boolean>>(async () => false)
export const useConfirm = () => useContext(ConfirmCtx)

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null); const [opts, setOpts] = useState<ConfirmOpts | null>(null)
  const settle = useRef<((v: boolean) => void) | null>(null); const back = useRef<HTMLElement | null>(null)
  const titleId = useId(); const bodyId = useId()
  const confirm = useCallback((o: ConfirmOpts) => new Promise<boolean>(resolve => {
    back.current = document.activeElement as HTMLElement | null; settle.current = resolve; setOpts(o)
  }), [])
  useEffect(() => { if (opts && ref.current && !ref.current.open) ref.current.showModal() }, [opts])
  const done = (v: boolean) => {
    ref.current?.close(); settle.current?.(v); settle.current = null; setOpts(null)
    back.current?.focus?.()                                   // Bible: restore focus where it was
  }
  return <ConfirmCtx.Provider value={confirm}>
    {children}
    <dialog ref={ref} aria-labelledby={opts ? titleId : undefined} aria-label={opts ? undefined : 'Confirmation'} aria-describedby={opts?.body ? bodyId : undefined} onCancel={e => { e.preventDefault(); done(false) }}
      className="dialog-motion m-auto w-[min(28rem,calc(100vw-2rem))] rounded-sheet border border-line bg-raised p-6 text-ink shadow-float backdrop:bg-scrim">
      {opts && <>
        <h2 id={titleId} className="text-base font-semibold">{opts.title}</h2>
        {opts.body && <div id={bodyId} className="mt-2 text-sm text-ink-2">{opts.body}</div>}
        <div className="mt-6 flex justify-end gap-2">
          <Btn kind="ghost" autoFocus onClick={() => done(false)}>{opts.cancelLabel ?? 'Cancel'}</Btn>
          <Btn kind={opts.tone === 'danger' ? 'danger' : 'primary'} onClick={() => done(true)}>{opts.confirmLabel}</Btn>
        </div>
      </>}
    </dialog>
  </ConfirmCtx.Provider>
}

// ------------------------------------------------------------------ toasts (non-blocking; errors persist; paused on hover/focus)
type Toast = { id: number; tone: Tone; text: string }
const ToastCtx = createContext<(tone: Tone, text: string) => void>(() => {})
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]); const seq = useRef(0)
  const push = useCallback((tone: Tone, text: string) => setItems(x => [...x.slice(-3), { id: ++seq.current, tone, text }]), [])
  const drop = useCallback((id: number) => setItems(x => x.filter(t => t.id !== id)), [])
  return <ToastCtx.Provider value={push}>
    {children}
    <div aria-live="polite" aria-relevant="additions" className="pointer-events-none fixed right-4 bottom-4 z-[var(--z-toast)] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2">
      {items.map(t => <ToastItem key={t.id} t={t} onClose={drop} />)}
    </div>
  </ToastCtx.Provider>
}

function ToastItem({ t, onClose }: { t: Toast; onClose: (id: number) => void }) {
  const [paused, setPaused] = useState(false); const life = toastLifetime(t.tone)
  useEffect(() => { if (life === null || paused) return; const h = setTimeout(() => onClose(t.id), life); return () => clearTimeout(h) }, [life, paused, onClose, t.id])
  const s = TONE_LABEL[t.tone]
  return <div role={t.tone === 'error' ? 'alert' : 'status'} onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} onFocus={() => setPaused(true)} onBlur={() => setPaused(false)}
    className={cx('toast-motion pointer-events-auto flex items-start gap-2 rounded-box border border-line bg-raised p-3 text-sm text-ink shadow-float')}>
    <span aria-hidden className={cx('mt-px flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold', TONE_STYLE[t.tone])}>{s.symbol}</span>
    <p className="min-w-0 flex-1"><span className="sr-only">{s.word}: </span>{t.text}</p>
    <button onClick={() => onClose(t.id)} aria-label="Dismiss" className={cx('-m-1 grid h-6 w-6 place-items-center rounded-field text-ink-3 hover:bg-surface hover:text-ink', MOTION)}>×</button>
  </div>
}
