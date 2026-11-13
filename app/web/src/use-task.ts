// Keeps one task fresh: asked for again while it is running or waiting, never after it has finished.
import { useCallback, useEffect, useState } from 'react'
import { pollMs, tasks, type Task } from './tasks'

/** Loads a task by id, poster or reel, and keeps it fresh while it is not finished. `tick` forces a reload after the screen reported a step. */
export function useTask(find: { id?: string; poster?: string; reel?: string }, tick = 0) {
  const [task, setTask] = useState<Task | null>(null); const [err, setErr] = useState<string | null>(null); const [loaded, setLoaded] = useState(false)
  const { id, poster, reel } = find
  const load = useCallback(() => (id ? tasks.get(id) : poster ? tasks.forPoster(poster) : reel ? tasks.forReel(reel) : Promise.resolve(null))
    .then(t => { setTask(t); setErr(null) }).catch(e => setErr((e as Error).message)).finally(() => setLoaded(true)), [id, poster, reel])
  useEffect(() => { load() }, [load, tick])
  const wait = pollMs(task)
  useEffect(() => { if (!wait) return; const h = setInterval(load, wait); return () => clearInterval(h) }, [wait, load])
  return { task, err, loaded, reload: load, setTask }
}

