// Shared UI pieces. Colours, radii, shadows and motion come only from design/tokens/tokens.css
// (via the short utility names in index.css). Never hard-code them here or in a screen.
export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(' ')
export const MOTION = 'transition duration-[var(--motion-fast)] ease-[var(--ease-out)]'

export function Btn({ kind = 'primary', className, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { kind?: 'primary' | 'ghost' | 'danger' | 'quiet' }) {
  return <button {...p} className={cx('inline-flex min-h-[var(--control-height)] items-center justify-center gap-1.5 rounded-btn px-[var(--control-padding-x)] text-sm font-semibold',
    MOTION, 'enabled:active:scale-[var(--press-scale)] disabled:cursor-not-allowed disabled:opacity-50',
    kind === 'primary' && 'bg-act text-on-act enabled:hover:bg-act-hover enabled:active:bg-act-pressed',
    kind === 'ghost' && 'border border-line-strong bg-raised text-ink enabled:hover:bg-act-subtle',
    kind === 'quiet' && 'text-ink-2 enabled:hover:bg-surface enabled:hover:text-ink',
    kind === 'danger' && 'bg-bad-solid text-on-act enabled:hover:bg-bad-solid-hover', className)} />
}

export function Card({ title, step, state, children, right }: { title: string; step?: number; state?: 'done' | 'next' | 'todo'; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section className={cx('rounded-box border bg-raised p-6 shadow-soft', state === 'next' ? 'border-act ring-1 ring-act' : 'border-line')}>
      <header className="mb-4 flex flex-wrap items-center gap-3">
        {step !== undefined && <span className={cx('flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold',
          state === 'done' ? 'bg-ok-subtle text-ok' : state === 'next' ? 'bg-act text-on-act' : 'bg-surface text-ink-3')}>{state === 'done' ? '✓' : step}</span>}
        <h2 className="text-base font-semibold">{title}</h2>
        <div className="ml-auto">{right}</div>
      </header>
      {children}
    </section>
  )
}

export const Pill = ({ ok, children }: { ok?: boolean | null; children: React.ReactNode }) =>
  <span className={cx('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', ok === true && 'bg-ok-subtle text-ok', ok === false && 'bg-bad-subtle text-bad', ok == null && 'bg-raised text-ink-2 ring-1 ring-inset ring-line')}>{children}</span>

export const Err = ({ msg }: { msg: string | null }) => msg ? <p role="alert" className="mt-2 rounded-field bg-bad-subtle px-3 py-2 text-sm text-bad">{msg}</p> : null

export const Select = ({ className, ...p }: React.SelectHTMLAttributes<HTMLSelectElement>) =>
  <select {...p} className={cx('min-h-9 max-w-full rounded-field border border-line-strong bg-raised px-2 py-1.5 text-sm text-ink', className)} />

export const Field = ({ className, ...p }: React.InputHTMLAttributes<HTMLInputElement>) =>
  <input {...p} className={cx('min-h-9 w-full rounded-field border border-line-strong bg-raised px-2 py-1.5 text-sm text-ink', className)} />

export function PageHead({ title, sub }: { title: string; sub?: string }) {
  return <header className="mb-6"><h1 className="font-head text-[length:var(--text-title)] leading-[var(--leading-title)] font-semibold tracking-[var(--tracking-title)]">{title}</h1>
    {sub && <p className="mt-1 text-sm text-ink-2">{sub}</p>}</header>
}
