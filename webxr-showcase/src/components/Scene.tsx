import { Suspense } from 'react'
import { OrbitControls, Environment, Grid } from '@react-three/drei'
import { ShowcaseModel } from './ShowcaseModel'
import * as THREE from 'three'

export function Scene({ inXR }: { inXR: boolean }) {
  return (
    <>
      {/* Solid background — replaces any passthrough leak with a deep blue */}
      <color attach="background" args={['#0c1426']} />

      <ambientLight intensity={0.4} />
      <directionalLight
        position={[5, 8, 5]}
        intensity={1.3}
        castShadow={!inXR}
        shadow-mapSize={[1024, 1024]}
      />
      <directionalLight position={[-5, 4, -3]} intensity={0.5} color="#9bbcff" />

      {/* Skybox + IBL — fills the entire 360° with a warehouse-like environment.
          `background` is enabled so users see lit walls when looking up/around
          instead of passthrough leaking through. */}
      <Suspense fallback={null}>
        <Environment preset="warehouse" background blur={0.2} />
      </Suspense>

      {/* Stable ground reference */}
      <Grid
        args={[50, 50]}
        cellSize={0.5}
        cellThickness={0.4}
        cellColor="#1a1d22"
        sectionSize={2}
        sectionThickness={1}
        sectionColor="#4a9eff"
        fadeDistance={30}
        position={[0, 0, 0]}
        infiniteGrid={false}
      />

      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        receiveShadow={!inXR}
      >
        <planeGeometry args={[40, 40]} />
        <meshStandardMaterial color="#0a0c10" metalness={0.1} roughness={0.95} />
      </mesh>

      <ShowcaseModel />

      {/* Non-VR camera controls (ignored in XR mode) */}
      {!inXR && (
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          minDistance={1}
          maxDistance={30}
          target={[0, 1.2, 0]}
          makeDefault
        />
      )}
    </>
  )
}
