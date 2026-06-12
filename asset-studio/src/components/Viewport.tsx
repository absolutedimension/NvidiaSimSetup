import { useRef, useMemo, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import {
  OrbitControls, Environment, Grid, Float, useTexture, useGLTF,
} from '@react-three/drei'
import * as THREE from 'three'
import { useStudio } from '../store/store'

function SpinningPlaceholder() {
  const ref = useRef<THREE.Mesh>(null!)
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * 0.4
  })
  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.6}>
      <mesh ref={ref} castShadow>
        <icosahedronGeometry args={[1, 1]} />
        <meshStandardMaterial
          color="#4a9eff"
          metalness={0.6}
          roughness={0.2}
          wireframe={false}
        />
      </mesh>
    </Float>
  )
}

function RenderedPlane({ url }: { url: string }) {
  const tex = useTexture(url)
  tex.colorSpace = THREE.SRGBColorSpace
  return (
    <Float speed={1} floatIntensity={0.3}>
      <mesh>
        <planeGeometry args={[3, 3]} />
        <meshBasicMaterial map={tex} toneMapped={false} side={THREE.DoubleSide} />
      </mesh>
    </Float>
  )
}

function CityModel({ url }: { url: string }) {
  // Fit longest dimension to ~10 m so a 1 km OSM block fits the orbit camera.
  const { scene } = useGLTF(url)
  const fitted = useMemo(() => {
    const root = scene.clone(true)
    const box = new THREE.Box3().setFromObject(root)
    const size = new THREE.Vector3()
    box.getSize(size)
    const longest = Math.max(size.x, size.y, size.z) || 1
    const scale = 10 / longest
    root.scale.setScalar(scale)
    // Re-center on the floor.
    box.setFromObject(root)
    const center = new THREE.Vector3()
    box.getCenter(center)
    root.position.x -= center.x
    root.position.z -= center.z
    root.position.y -= box.min.y
    return root
  }, [scene])
  return <primitive object={fitted} />
}

export function Viewport() {
  const { outputRenderUrl, outputGlbUrl } = useStudio()

  const cacheBustedRender = useMemo(() => {
    if (!outputRenderUrl) return null
    return `${outputRenderUrl}${outputRenderUrl.includes('?') ? '&' : '?'}t=${Date.now()}`
  }, [outputRenderUrl])

  const cacheBustedGlb = useMemo(() => {
    if (!outputGlbUrl) return null
    return `${outputGlbUrl}${outputGlbUrl.includes('?') ? '&' : '?'}t=${Date.now()}`
  }, [outputGlbUrl])

  const showGlb = !!cacheBustedGlb
  const orbitMax = showGlb ? 80 : 20

  return (
    <Canvas
      shadows
      camera={{ position: showGlb ? [15, 10, 15] : [3, 2, 5], fov: 45 }}
      style={{ width: '100%', height: '100%' }}
    >
      <color attach="background" args={['#0b0d10']} />
      <fog attach="fog" args={['#0b0d10', showGlb ? 40 : 8, showGlb ? 120 : 20]} />

      <ambientLight intensity={0.3} />
      <directionalLight
        position={[5, 8, 5]}
        intensity={1.2}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />

      <Suspense fallback={null}>
        {cacheBustedGlb ? (
          <CityModel url={cacheBustedGlb} />
        ) : cacheBustedRender ? (
          <RenderedPlane url={cacheBustedRender} />
        ) : (
          <SpinningPlaceholder />
        )}

        <Grid
          args={[20, 20]}
          cellSize={0.5}
          cellThickness={0.5}
          cellColor="#1a1d22"
          sectionSize={2}
          sectionThickness={1}
          sectionColor="#4a9eff"
          fadeDistance={showGlb ? 60 : 20}
          position={[0, showGlb ? -0.01 : -1.5, 0]}
          infiniteGrid
        />

        <Environment preset="studio" />
      </Suspense>

      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        minDistance={2}
        maxDistance={orbitMax}
        target={[0, showGlb ? 1 : 0, 0]}
      />
    </Canvas>
  )
}
