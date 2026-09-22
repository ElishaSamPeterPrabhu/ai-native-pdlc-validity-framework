import { Canvas, useFrame } from '@react-three/fiber';
import { ContactShadows, OrbitControls, Text } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import {
  BALL_RADIUS,
  boosterConfig,
  rampConfigs,
  RAMP_LENGTH,
  RAMP_WIDTH,
  totalRunDuration,
  USER_BUCKET_POSITION,
  type MarbleRunVariant,
  type RampConfig,
} from './rolling-track-3d';

interface SceneProps {
  variant: MarbleRunVariant;
  reducedMotion: boolean;
}

function Ramp({ ramp, boost }: { ramp: RampConfig; boost: boolean }) {
  return (
    <group position={ramp.position} rotation={[0, 0, -ramp.tilt]}>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[RAMP_LENGTH, 0.18, RAMP_WIDTH]} />
        <meshStandardMaterial color={ramp.color} metalness={0.25} roughness={0.32} emissive={boost ? ramp.color : '#000000'} emissiveIntensity={boost ? 0.12 : 0} />
      </mesh>
      <mesh position={[-0.75, 0.16, 0]} castShadow>
        <boxGeometry args={[0.14, 0.28, RAMP_WIDTH]} />
        <meshStandardMaterial color={ramp.color} />
      </mesh>
      <Text position={[0, 0.26, 0]} rotation={[0, 0, ramp.tilt]} fontSize={0.22} color="#eef1f6" anchorX="center" anchorY="middle">
        {ramp.name}
      </Text>
    </group>
  );
}

function UserBucket() {
  return (
    <group position={USER_BUCKET_POSITION}>
      <mesh position={[0, 0.35, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.8, 0.58, 0.7, 32, 1, true]} />
        <meshStandardMaterial color="#8a96a8" metalness={0.65} roughness={0.25} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 0.72, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.8, 0.07, 12, 32]} />
        <meshStandardMaterial color="#d8e0eb" metalness={0.75} roughness={0.2} />
      </mesh>
      <Text position={[0, 1.05, 0]} fontSize={0.24} color="#eef1f6" anchorX="center">
        User
      </Text>
    </group>
  );
}

function Booster({ active }: { active: boolean }) {
  return (
    <group position={boosterConfig.position}>
      <mesh rotation={[0, 0, -0.25]} castShadow>
        <boxGeometry args={[0.7, 0.16, 0.55]} />
        <meshStandardMaterial color={boosterConfig.color} emissive={boosterConfig.color} emissiveIntensity={active ? 0.8 : 0.18} metalness={0.35} />
      </mesh>
      <Text position={[0, 0.3, 0]} fontSize={0.18} color="#ffda8b" anchorX="center">
        BOOST
      </Text>
    </group>
  );
}

function Marble({ variant, reducedMotion }: SceneProps) {
  const ballRef = useRef<THREE.Mesh>(null);
  const elapsedRef = useRef(0);
  const ramps = rampConfigs[variant];
  const duration = totalRunDuration(variant);

  const path = useMemo(() => {
    const points: THREE.Vector3[] = [];
    ramps.forEach((ramp) => {
      points.push(new THREE.Vector3(ramp.position[0] - 0.95, ramp.position[1] + 0.42, 0));
      points.push(new THREE.Vector3(ramp.position[0] + 0.95, ramp.position[1] - 0.12, 0));
    });
    points.push(new THREE.Vector3(USER_BUCKET_POSITION[0], 2.0, 0));
    points.push(new THREE.Vector3(USER_BUCKET_POSITION[0], 0.55, 0));
    return points;
  }, [ramps]);

  useFrame((_, delta) => {
    const ball = ballRef.current;
    if (!ball) return;
    if (reducedMotion) {
      ball.position.set(USER_BUCKET_POSITION[0], 0.62, 0);
      return;
    }
    elapsedRef.current = (elapsedRef.current + delta) % duration;
    const t = elapsedRef.current / duration;
    const scaled = t * (path.length - 1);
    const index = Math.min(path.length - 2, Math.floor(scaled));
    const localT = scaled - index;
    const eased = localT * localT * (3 - 2 * localT);
    ball.position.lerpVectors(path[index], path[index + 1], eased);
    ball.rotation.z -= delta * 8;
    ball.rotation.x -= delta * 5;
  });

  return (
    <mesh ref={ballRef} position={[path[0].x, path[0].y, path[0].z]} castShadow>
      <sphereGeometry args={[BALL_RADIUS, 32, 20]} />
      <meshStandardMaterial color="#f3b94f" metalness={0.72} roughness={0.18} />
    </mesh>
  );
}

function SceneContents({ variant, reducedMotion }: SceneProps) {
  const boost = variant === 'aiBoost';
  return (
    <>
      <color attach="background" args={['#11151c']} />
      <ambientLight intensity={1.2} />
      <directionalLight position={[3, 7, 5]} intensity={2.4} castShadow />
      <pointLight position={[3, 2, 2]} color={boost ? '#f3b94f' : '#62b0ff'} intensity={boost ? 2 : 0.8} />
      {rampConfigs[variant].map((ramp) => <Ramp key={ramp.name} ramp={ramp} boost={boost} />)}
      {boost ? <Booster active={!reducedMotion} /> : null}
      <UserBucket />
      <Marble variant={variant} reducedMotion={reducedMotion} />
      <ContactShadows position={[0, -0.02, 0]} opacity={0.4} scale={14} blur={2.5} far={5} />
      <OrbitControls enablePan={false} enableZoom={false} maxPolarAngle={Math.PI / 2.1} minPolarAngle={Math.PI / 3.5} />
    </>
  );
}

export function RollingTrack3DScene({ variant, reducedMotion }: SceneProps) {
  return (
    <Canvas shadows dpr={[1, 2]} camera={{ position: [0, 5.3, 10], fov: 42 }}>
      <SceneContents variant={variant} reducedMotion={reducedMotion} />
    </Canvas>
  );
}
