import { useEffect, useMemo, useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import { Billboard, Text } from '@react-three/drei'
import * as THREE from 'three'
import { useStore } from '../store/store'

/**
 * Renders an AMP-style trajectory (T x 15 body positions per frame) as a
 * stick figure: spheres at each body, cylinders for the kinematic-tree
 * connections. Used to visualize the dance mocap reference clip and (later)
 * policy rollouts in WebXR without needing a Blender → GLB export step.
 *
 * Trajectory JSON contract (produced by mocap_handoff/npz_to_webxr_trajectory.py):
 *   {
 *     label, source_fps, playback_fps,
 *     frames: T,
 *     body_names: string[15],
 *     parents: int[15],          // -1 for root
 *     positions: float[T*15*3],  // already Y-up Three.js, in meters
 *   }
 */

type Trajectory = {
  label: string
  source_fps: number
  playback_fps: number
  frames: number
  body_names: string[]
  parents: number[]
  positions: number[]
}

const SPHERE_RADIUS = 0.06 // m
const BONE_RADIUS = 0.03   // m
const COLOR_BODY = '#4a9eff'
const COLOR_BONE = '#9aa4b2'
const COLOR_PELVIS = '#ffcf4a'

/** Position a unit-Y cylinder so it spans [a → b]. */
function alignCylinder(mesh: THREE.Object3D, a: THREE.Vector3, b: THREE.Vector3) {
  const mid = new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5)
  const dir = new THREE.Vector3().subVectors(b, a)
  const length = dir.length()
  mesh.position.copy(mid)
  mesh.scale.set(1, length || 1e-6, 1)
  // unit-Y → align with dir
  const up = new THREE.Vector3(0, 1, 0)
  const axis = new THREE.Vector3().crossVectors(up, dir.clone().normalize())
  const angle = Math.acos(THREE.MathUtils.clamp(up.dot(dir.clone().normalize()), -1, 1))
  if (axis.lengthSq() > 1e-8) {
    mesh.quaternion.setFromAxisAngle(axis.normalize(), angle)
  } else {
    mesh.quaternion.identity()
  }
}

export function StickFigureAnimation({
  trajectoryUrl,
  yOffset = 0,
}: {
  trajectoryUrl: string
  yOffset?: number
}) {
  const [traj, setTraj] = useState<Trajectory | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const setLoaded = useStore((s) => s.setLoaded)

  // ref arrays for body spheres + bone cylinders, populated on mount
  const sphereRefs = useRef<Array<THREE.Mesh | null>>([])
  const boneRefs = useRef<Array<THREE.Mesh | null>>([])
  const tStart = useRef<number>(performance.now() / 1000)

  useEffect(() => {
    let cancelled = false
    fetch(trajectoryUrl)
      .then((r) => {
        if (!r.ok) throw new Error(`fetch ${r.status}`)
        return r.json()
      })
      .then((j: Trajectory) => {
        if (cancelled) return
        setTraj(j)
        setLoaded(true)
        // eslint-disable-next-line no-console
        console.log(
          `[StickFigure] loaded "${j.label}" — ` +
            `${j.frames} frames @ ${j.playback_fps} fps ` +
            `(${(j.frames / j.playback_fps).toFixed(1)} s)`,
        )
      })
      .catch((e) => !cancelled && setErr(e.message))
    return () => {
      cancelled = true
      setLoaded(false)
    }
  }, [trajectoryUrl, setLoaded])

  const bones = useMemo(() => {
    if (!traj) return []
    return traj.parents
      .map((parent, child) => ({ child, parent }))
      .filter((b) => b.parent >= 0)
  }, [traj])

  useFrame(() => {
    if (!traj) return
    const elapsed = performance.now() / 1000 - tStart.current
    const totalFrames = traj.frames
    const frameF = (elapsed * traj.playback_fps) % totalFrames
    const f0 = Math.floor(frameF)
    const f1 = (f0 + 1) % totalFrames
    const t = frameF - f0

    const stride = 15 * 3
    const pos = traj.positions
    // interp + place spheres
    const tmpA = new THREE.Vector3()
    const tmpB = new THREE.Vector3()
    for (let i = 0; i < 15; i++) {
      const a = f0 * stride + i * 3
      const b = f1 * stride + i * 3
      const x = pos[a] * (1 - t) + pos[b] * t
      const y = pos[a + 1] * (1 - t) + pos[b + 1] * t
      const z = pos[a + 2] * (1 - t) + pos[b + 2] * t
      const m = sphereRefs.current[i]
      if (m) m.position.set(x, y, z)
    }
    // re-orient bones
    for (let k = 0; k < bones.length; k++) {
      const { child, parent } = bones[k]
      const ms = sphereRefs.current
      const a = ms[parent]
      const b = ms[child]
      if (!a || !b) continue
      tmpA.copy(a.position)
      tmpB.copy(b.position)
      const mb = boneRefs.current[k]
      if (mb) alignCylinder(mb, tmpA, tmpB)
    }
  })

  if (err) {
    return (
      <Billboard position={[0, 1.5, -2.0]} follow>
        <Text fontSize={0.22} color="#ff5470" anchorX="center" anchorY="middle">
          Trajectory load failed
        </Text>
        <Text
          position={[0, -0.35, 0]}
          fontSize={0.08}
          color="#9aa4b2"
          anchorX="center"
          anchorY="middle"
        >
          {err}
        </Text>
      </Billboard>
    )
  }

  if (!traj) {
    return (
      <Billboard position={[0, 1.5, -2.0]} follow>
        <Text fontSize={0.22} color="#4a9eff" anchorX="center" anchorY="middle">
          Loading dance trajectory…
        </Text>
      </Billboard>
    )
  }

  return (
    <group position={[0, yOffset, 0]}>
      {/* Body joint spheres */}
      {traj.body_names.map((name, i) => (
        <mesh
          key={`s-${i}`}
          ref={(m) => (sphereRefs.current[i] = m)}
        >
          <sphereGeometry args={[SPHERE_RADIUS, 12, 12]} />
          <meshStandardMaterial
            color={i === 0 ? COLOR_PELVIS : COLOR_BODY}
            roughness={0.5}
            metalness={0.1}
          />
        </mesh>
      ))}
      {/* Bones */}
      {bones.map((b, k) => (
        <mesh
          key={`b-${k}`}
          ref={(m) => (boneRefs.current[k] = m)}
        >
          <cylinderGeometry args={[BONE_RADIUS, BONE_RADIUS, 1, 8]} />
          <meshStandardMaterial color={COLOR_BONE} roughness={0.6} />
        </mesh>
      ))}
      {/* Label below */}
      <Billboard position={[0, -0.1, 0]} follow>
        <Text fontSize={0.12} color="#cfd8e3" anchorX="center" anchorY="middle">
          {traj.label}
        </Text>
        <Text
          position={[0, -0.18, 0]}
          fontSize={0.07}
          color="#7a8593"
          anchorX="center"
          anchorY="middle"
        >
          {`${traj.frames} frames · ${(traj.frames / traj.playback_fps).toFixed(1)} s · ${traj.playback_fps} fps`}
        </Text>
      </Billboard>
    </group>
  )
}
