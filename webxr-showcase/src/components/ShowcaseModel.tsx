import {
  Suspense,
  useEffect,
  useMemo,
  useRef,
  Component,
  type ReactNode,
} from 'react'
// (useRef already imported above; useAnimations attaches to its ref)
import { useGLTF, useAnimations, Text, Billboard } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useStore } from '../store/store'
import { StickFigureAnimation } from './StickFigureAnimation'

const TARGET_SIZE = 3 // longest dim auto-scaled to ~3 m

/**
 * In-scene loading indicator. Visible in BOTH desktop and VR
 * (uses drei's <Text> + <Billboard> so it always faces the viewer).
 * Rotating torus = spinner, gives users a clear "wait" cue.
 */
function LoadingIndicator() {
  const ring = useRef<THREE.Mesh>(null)
  const showcases = useStore((s) => s.showcases)
  const selectedId = useStore((s) => s.selectedId)
  const label = showcases.find((s) => s.id === selectedId)?.label ?? 'asset'

  useFrame((_, dt) => {
    if (ring.current) ring.current.rotation.z += dt * 2.0
  })

  return (
    <Billboard position={[0, 1.5, -2.0]} follow>
      <Text fontSize={0.22} color="#4a9eff" anchorX="center" anchorY="middle">
        {`Loading ${label}…`}
      </Text>
      <mesh ref={ring} position={[0, -0.45, 0]}>
        <torusGeometry args={[0.28, 0.025, 16, 64, Math.PI * 1.5]} />
        <meshBasicMaterial color="#4a9eff" toneMapped={false} />
      </mesh>
      <Text
        position={[0, -0.85, 0]}
        fontSize={0.08}
        color="#9aa4b2"
        anchorX="center"
        anchorY="middle"
      >
        large assets can take 30–60 s
      </Text>
    </Billboard>
  )
}

/**
 * Shown only when the asset failed to load entirely (ErrorBoundary fallback).
 * Red, with explicit "Failed" text so it's obviously not a normal state.
 */
function ErrorIndicator() {
  return (
    <Billboard position={[0, 1.5, -2.0]} follow>
      <Text fontSize={0.22} color="#ff5470" anchorX="center" anchorY="middle">
        Failed to load
      </Text>
      <mesh position={[0, -0.45, 0]}>
        <boxGeometry args={[0.4, 0.4, 0.4]} />
        <meshStandardMaterial color="#ff5470" metalness={0.2} roughness={0.4} />
      </mesh>
      <Text
        position={[0, -0.85, 0]}
        fontSize={0.08}
        color="#9aa4b2"
        anchorX="center"
        anchorY="middle"
      >
        check the HUD for the error message
      </Text>
    </Billboard>
  )
}

function Model({ url, yOffset }: { url: string; yOffset: number }) {
  const gltf = useGLTF(url) as any
  const { scene, animations } = gltf
  const groupRef = useRef<THREE.Group>(null)
  const { actions, names } = useAnimations(animations ?? [], groupRef)
  const setLoaded = useStore((s) => s.setLoaded)

  const { center, scale, height } = useMemo(() => {
    const box = new THREE.Box3().setFromObject(scene)
    const size = new THREE.Vector3()
    box.getSize(size)
    const center = new THREE.Vector3()
    box.getCenter(center)
    const maxDim = Math.max(size.x, size.y, size.z) || 1
    const scale = TARGET_SIZE / maxDim
    const height = size.y * scale
    return { center, scale, height }
  }, [scene])

  useEffect(() => {
    setLoaded(true)
    return () => setLoaded(false)
  }, [setLoaded, url])

  // Auto-play the first embedded glTF animation clip on a loop.
  // Drone GLBs (cf2x_trained.glb) carry the baked trained-policy trajectory
  // as a single NLA-strip clip; static GLBs (warehouse, ragnarok) have
  // no animations and this is a no-op.
  useEffect(() => {
    if (!names.length) return
    const action = actions[names[0]]
    if (!action) return
    action.reset()
    action.setLoop(THREE.LoopRepeat, Infinity)
    action.clampWhenFinished = false
    action.timeScale = 1.0
    action.play()
    // eslint-disable-next-line no-console
    console.log(
      `[ShowcaseModel] playing animation "${names[0]}" ` +
        `(${animations[0]?.duration.toFixed(2)}s, ${names.length} clip(s) total)`,
    )
    return () => {
      action.stop()
    }
  }, [actions, names, animations])

  return (
    <group ref={groupRef} position={[0, yOffset, 0]}>
      <group
        scale={scale}
        position={[
          -center.x * scale,
          -center.y * scale + height / 2,
          -center.z * scale,
        ]}
      >
        <primitive object={scene} />
      </group>
    </group>
  )
}

class ErrorBoundary extends Component<{
  children: ReactNode
  onError: (msg: string) => void
}> {
  state = { hasError: false }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  componentDidCatch(err: Error) {
    this.props.onError(err.message)
  }
  render() {
    if (this.state.hasError) return <ErrorIndicator />
    return this.props.children
  }
}

export function ShowcaseModel() {
  const showcases = useStore((s) => s.showcases)
  const selectedId = useStore((s) => s.selectedId)
  const setError = useStore((s) => s.setError)
  const showcase = showcases.find((s) => s.id === selectedId)

  if (!showcase) return <LoadingIndicator />

  // Optional companion (side-by-side comparison)
  const compareXOffset = showcase.compareXOffset ?? 1.5
  const hasCompare = !!(showcase.compareTrajectoryUrl || showcase.compareGlbUrl)
  const primaryX = hasCompare ? -compareXOffset / 2 : 0
  const compareX = compareXOffset / 2

  return (
    <ErrorBoundary onError={setError}>
      {/* Primary slot */}
      <group position={[primaryX, 0, 0]}>
        {showcase.trajectoryUrl ? (
          <StickFigureAnimation
            key={`${showcase.id}-primary`}
            trajectoryUrl={showcase.trajectoryUrl}
            yOffset={showcase.yOffset ?? 0}
          />
        ) : showcase.glbUrl ? (
          <Suspense fallback={<LoadingIndicator />}>
            <Model
              key={`${showcase.id}-primary`}
              url={showcase.glbUrl}
              yOffset={showcase.yOffset ?? 0}
            />
          </Suspense>
        ) : (
          <LoadingIndicator />
        )}
      </group>
      {/* Companion slot */}
      {hasCompare && (
        <group position={[compareX, 0, 0]}>
          {showcase.compareTrajectoryUrl ? (
            <StickFigureAnimation
              key={`${showcase.id}-compare`}
              trajectoryUrl={showcase.compareTrajectoryUrl}
              yOffset={showcase.yOffset ?? 0}
            />
          ) : showcase.compareGlbUrl ? (
            <Suspense fallback={<LoadingIndicator />}>
              <Model
                key={`${showcase.id}-compare`}
                url={showcase.compareGlbUrl}
                yOffset={showcase.yOffset ?? 0}
              />
            </Suspense>
          ) : null}
        </group>
      )}
    </ErrorBoundary>
  )
}
