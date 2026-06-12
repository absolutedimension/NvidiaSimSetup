import type { Showcase } from '../store/store'

const FALLBACK: Showcase[] = [
  {
    id: 'placeholder',
    label: 'Placeholder Cube',
    glbUrl: '',
    description: 'GLB assets not converted yet — waiting on EC2 backend',
    scale: 1,
    yOffset: 1.2,
  },
]

export async function loadShowcaseManifest(
  manifestUrl: string = '/assets/manifest.json',
): Promise<Showcase[]> {
  try {
    const res = await fetch(manifestUrl, { cache: 'no-store' })
    if (!res.ok) throw new Error(`manifest http ${res.status}`)
    const data = await res.json()
    if (Array.isArray(data?.showcases)) return data.showcases as Showcase[]
    if (Array.isArray(data)) return data as Showcase[]
    return FALLBACK
  } catch {
    return FALLBACK
  }
}
