import { useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { XR, createXRStore } from '@react-three/xr'
import { Loader } from '@react-three/drei'
import { Scene } from './components/Scene'
import { HUD } from './components/HUD'

const xrStore = createXRStore({
  emulate: false,
  controller: { teleportPointer: true },
  hand: { teleportPointer: true },
})

export function App() {
  const [inXR, setInXR] = useState(false)

  useEffect(() => {
    const unsubscribe = xrStore.subscribe((state) => {
      setInXR(state.session !== null)
    })
    return unsubscribe
  }, [])

  const enterVR = () => xrStore.enterVR()

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <Canvas
        shadows
        camera={{ position: [3, 1.7, 4], fov: 55 }}
        gl={{
          antialias: true,
          alpha: false,                  // opaque canvas = no passthrough leak
          powerPreference: 'high-performance',
        }}
        style={{ width: '100%', height: '100%' }}
      >
        <XR store={xrStore}>
          <Scene inXR={inXR} />
        </XR>
      </Canvas>
      <HUD isXR={inXR} onEnterVR={enterVR} />
      {/* drei Loader = desktop CSS overlay with auto progress bar.
          Doesn't render in VR (immersive session takes over the canvas) —
          the in-scene LoadingIndicator in ShowcaseModel covers that. */}
      <Loader
        containerStyles={{
          background: 'rgba(15, 17, 22, 0.85)',
          backdropFilter: 'blur(14px)',
        }}
        innerStyles={{ background: 'rgba(74,158,255,0.25)' }}
        barStyles={{ background: '#4a9eff', height: 4 }}
        dataStyles={{
          color: '#e4e6eb',
          fontSize: 12,
          fontFamily: 'system-ui, -apple-system, sans-serif',
          letterSpacing: 0.3,
          marginTop: 8,
        }}
        dataInterpolation={(p) => `Loading… ${p.toFixed(0)}%`}
      />
    </div>
  )
}
