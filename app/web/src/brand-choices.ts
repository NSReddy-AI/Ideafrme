// Brand kits a new poster may use: only approved brands with current rights (M5 eligibility). Drafts are listed
// separately so screens can show them as not available. Shared by Home and Advanced Create.
import { useEffect, useState } from 'react'
import { brands as brandApi } from './brands'
import { creative } from './creative'

export type EligibleBrand = { hash: string; name: string; revision: number }
export function useBrandChoices(): { usable: EligibleBrand[]; unavailable: { hash: string; name: string }[]; loaded: boolean } {
  const [usable, setUsable] = useState<EligibleBrand[] | null>(null)
  const [unavailable, setUnavailable] = useState<{ hash: string; name: string }[]>([])
  useEffect(() => {
    creative.eligibleBrands().then(v => setUsable(v.filter(x => x.eligible).map(x => ({ hash: x.hash, name: x.name, revision: x.revision })))).catch(() => setUsable([]))
    brandApi.list().then(l => setUnavailable(l.brands.filter(b => b.record.state !== 'approved' || !b.approval_current).map(b => ({ hash: b.hash, name: b.record.payload.name })))).catch(() => {})
  }, [])
  return { usable: usable ?? [], unavailable, loaded: usable !== null }
}
