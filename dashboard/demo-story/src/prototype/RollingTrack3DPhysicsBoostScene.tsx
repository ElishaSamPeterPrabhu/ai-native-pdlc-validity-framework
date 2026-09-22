import { BallCollider, CuboidCollider, Physics, RigidBody } from '@react-three/rapier';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import { useRef } from 'react';
import * as THREE from 'three';

const RAMP_LENGTH = 2.5;
const TRANSFER_GAP = 0.14;
const VERTICAL_DROP = 0.18;
const BALL_RADIUS = 0.23;
const rampAngles = [-0.18, -0.28, -0.38];
const rampNames = ['Product', 'Design', 'Engineering'];
const rampColors = ['#62b0ff', '#b494ff', '#42d477'];

type RampConfig = {
  name: string;
  position: [number, number, number];
  rotation: [number, number, number];
  color: string;
};

function endpoint(position: [number, number, number], angle: number) {
  return {
    x: position[0] + Math.cos(angle) * RAMP_LENGTH / 2,
    y: position[1] + Math.sin(angle) * RAMP_LENGTH / 2,
  };
}

const ramps: RampConfig[] = [];
let nextStart = { x: -4.25, y: 2.8 };
for (let index = 0; index < rampAngles.length; index += 1) {
  const angle = rampAngles[index];
  const position: [number, number, number] = [
    nextStart.x + Math.cos(angle) * RAMP_LENGTH / 2,
    nextStart.y + Math.sin(angle) * RAMP_LENGTH / 2,
    0,
  ];
  ramps.push({
    name: rampNames[index],
    position,
    rotation: [0, 0, angle],
    color: rampColors[index],
  });
  const exit = endpoint(position, angle);
  nextStart = { x: exit.x + TRANSFER_GAP, y: exit.y - VERTICAL_DROP };
}

const engineeringExit = endpoint(ramps[2].position, rampAngles[2]);
const bucketPosition: [number, number, number] = [engineeringExit.x + 2.0, engineeringExit.y - 1.25, 0];
const boostTriggerX = engineeringExit.x - 0.3;

function FixedTrack({ track, accent = false }: { track: RampConfig; accent?: boolean }) {
  return (
    <>
      <RigidBody type="fixed" colliders={false} position={track.position} rotation={track.rotation}>
        <mesh castShadow receiveShadow>
          <boxGeometry args={[RAMP_LENGTH, 0.18, 1.8]} />
          <meshStandardMaterial color={track.color} metalness={0.3} roughness={0.28} emissive={accent ? '#f3b94f' : '#000000'} emissiveIntensity={accent ? 0.3 : 0} />
        </mesh>
        <CuboidCollider args={[RAMP_LENGTH / 2, 0.09, 0.9]} />
      </RigidBody>
      <Text position={[track.position[0], track.position[1] + .7, track.position[2]]} rotation={[0, 0, -track.rotation[1]]} fontSize={0.2} color="#eef1f6" anchorX="center">
        {track.name}
      </Text>
    </>
  );
}

function AcceleratorGate() {
  return (
    <group position={[boostTriggerX, engineeringExit.y + 0.16, 0]}>
      <mesh rotation={[0, 0, -0.25]} castShadow>
        <boxGeometry args={[0.55, 0.12, 1.25]} />
        <meshStandardMaterial color="#f3b94f" emissive="#f3b94f" emissiveIntensity={0.7} metalness={0.45} />
      </mesh>
      <Text position={[.8, 0.65, 1.0]} fontSize={0.18} color="#ffda8b" anchorX="center">ACCELERATE</Text>
    </group>
  );
}

function UserBucket() {
  return (
    <group>
      <RigidBody type="fixed" colliders={false} position={bucketPosition}>
        <CuboidCollider args={[0.75, 0.12, 0.9]} position={[0, -0.35, 0]} />
        <CuboidCollider args={[0.12, 0.45, 0.9]} position={[-0.7, 0.1, 0]} />
        <CuboidCollider args={[0.12, 0.45, 0.9]} position={[0.7, 0.1, 0]} />
      </RigidBody>
      <mesh position={bucketPosition} castShadow>
        <cylinderGeometry args={[0.82, 0.6, 0.7, 32, 1, true]} />
        <meshStandardMaterial color="#8a96a8" metalness={0.7} roughness={0.22} side={THREE.DoubleSide} />
      </mesh>
      <Text position={[bucketPosition[0], bucketPosition[1] + 1.0, 0]} fontSize={0.24} color="#eef1f6" anchorX="center">User</Text>
    </group>
  );
}

function BoostBall() {
  const bodyRef = useRef<any>(null);
  const boostApplied = useRef(false);
  const resetTimer = useRef(0);
  const spawn = { x: ramps[0].position[0], y: ramps[0].position[1] + 0.7, z: 0 };

  useFrame((_, delta) => {
    const body = bodyRef.current;
    if (!body) return;
    const position = body.translation();
    if (!boostApplied.current && position.x > boostTriggerX && position.y < engineeringExit.y + 0.5) {
      body.setLinvel({ x: 3.9, y: -0.55, z: 0 }, true);
      boostApplied.current = true;
    }
    if (position.y < -2.5 || position.x > bucketPosition[0] + 1) {
      resetTimer.current += delta;
      if (resetTimer.current > 0.8) {
        body.setTranslation(spawn, true);
        body.setLinvel({ x: 0, y: 0, z: 0 }, true);
        body.setAngvel({ x: 0, y: 0, z: 0 }, true);
        boostApplied.current = false;
        resetTimer.current = 0;
      }
    } else {
      resetTimer.current = 0;
    }
  });

  return (
    <RigidBody ref={bodyRef} colliders={false} position={[spawn.x, spawn.y, spawn.z]} restitution={0.08} friction={1} linearDamping={0.55}>
      <BallCollider args={[BALL_RADIUS]} />
      <mesh castShadow>
        <sphereGeometry args={[BALL_RADIUS, 32, 20]} />
        <meshStandardMaterial color="#f3b94f" metalness={0.75} roughness={0.16} />
      </mesh>
    </RigidBody>
  );
}

export function RollingTrack3DPhysicsBoostScene() {
  return (
    <Canvas shadows camera={{ position: [0, 4.5, 10], fov: 42 }}>
      <color attach="background" args={['#11151c']} />
      <ambientLight intensity={1.1} />
      <directionalLight position={[3, 7, 5]} intensity={2.5} castShadow />
      <Physics gravity={[0, -9.81, 0]} interpolate>
        {ramps.map((ramp) => <FixedTrack key={ramp.name} track={ramp} />)}
        <AcceleratorGate />
        <UserBucket />
        <BoostBall />
        <RigidBody type="fixed" position={[0, -1.05, 0]}>
          <CuboidCollider args={[8, 0.1, 3]} />
        </RigidBody>
      </Physics>
      <OrbitControls enablePan={false} enableZoom={false} maxPolarAngle={Math.PI / 2.05} minPolarAngle={Math.PI / 3.5} />
    </Canvas>
  );
}
