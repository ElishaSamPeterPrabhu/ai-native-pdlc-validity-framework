import { Physics, RigidBody, CuboidCollider, BallCollider } from '@react-three/rapier';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import { useRef } from 'react';
import * as THREE from 'three';

const RAMP_LENGTH = 2.5;
const TRANSFER_GAP = 0.14;
const VERTICAL_DROP = 0.18;
const BALL_RADIUS = 0.23;
const rampAngles = [-0.18, -0.28, -0.38];
const rampNames = ['Product · flat', 'Design · tilted', 'Engineering'];
const rampColors = ['#62b0ff', '#b494ff', '#42d477'];

type RampConfig = {
  name: string;
  position: [number, number, number];
  rotation: [number, number, number];
  color: string;
};

function endpoint(position: [number, number, number], angle: number, side: 1 | -1) {
  return {
    x: position[0] + Math.cos(angle) * side * RAMP_LENGTH / 2,
    y: position[1] + Math.sin(angle) * side * RAMP_LENGTH / 2,
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
  const exit = endpoint(position, angle, 1);
  nextStart = { x: exit.x + TRANSFER_GAP, y: exit.y - VERTICAL_DROP };
}

const engineeringExit = endpoint(ramps[2].position, rampAngles[2], 1);
const bucketPosition: [number, number, number] = [engineeringExit.x + 0.95, engineeringExit.y - 0.85, 0];

function Ramp({ ramp }: { ramp: typeof ramps[number] }) {
  return (
    <>
      <RigidBody type="fixed" colliders={false} position={ramp.position} rotation={ramp.rotation}>
        <mesh castShadow receiveShadow>
          <boxGeometry args={[RAMP_LENGTH, 0.18, 1.8]} />
          <meshStandardMaterial color={ramp.color} metalness={0.25} roughness={0.3} />
        </mesh>
        <CuboidCollider args={[1.25, 0.09, 0.9]} />
      </RigidBody>
      <Text position={[ramp.position[0], ramp.position[1] + 0.25, ramp.position[2]]} rotation={[0, 0, -ramp.rotation[2]]} fontSize={0.2} color="#eef1f6" anchorX="center">
        {ramp.name}
      </Text>
    </>
  );
}

function Bucket() {
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
      <Text position={[bucketPosition[0], 1.15, 0]} fontSize={0.24} color="#eef1f6" anchorX="center">User</Text>
    </group>
  );
}

function PhysicsBall() {
  const bodyRef = useRef<any>(null);
  const resetTimer = useRef(0);
  const spawnPosition = {
    x: ramps[0].position[0],
    y: ramps[0].position[1] + 0.7,
    z: 0,
  };
  useFrame((_, delta) => {
    const body = bodyRef.current;
    if (!body) return;
    const position = body.translation();
    if (position.y < -2.5 || position.x > bucketPosition[0] + 1) {
      resetTimer.current += delta;
      if (resetTimer.current > 0.8) {
        body.setTranslation(spawnPosition, true);
        body.setLinvel({ x: 0.7, y: 0, z: 0 }, true);
        body.setAngvel({ x: 0, y: 0, z: 0 }, true);
        resetTimer.current = 0;
      }
    } else {
      resetTimer.current = 0;
    }
  });
  return (
    <RigidBody
      ref={bodyRef}
      colliders={false}
      position={[spawnPosition.x, spawnPosition.y, spawnPosition.z]}
      restitution={0.12}
      friction={1}
      linearDamping={0.2}
    >
      <BallCollider args={[BALL_RADIUS]} />
      <mesh castShadow>
        <sphereGeometry args={[BALL_RADIUS, 32, 20]} />
        <meshStandardMaterial color="#f3b94f" metalness={0.75} roughness={0.16} />
      </mesh>
    </RigidBody>
  );
}

export function RollingTrack3DPhysicsScene() {
  return (
    <Canvas shadows camera={{ position: [0, 4.5, 10], fov: 42 }}>
      <color attach="background" args={['#11151c']} />
      <ambientLight intensity={1.1} />
      <directionalLight position={[3, 7, 5]} intensity={2.5} castShadow />
      <Physics gravity={[0, -9.81, 0]} interpolate>
        {ramps.map((ramp) => <Ramp key={ramp.name} ramp={ramp} />)}
        <Bucket />
        <PhysicsBall />
        <RigidBody type="fixed" position={[0, -1.05, 0]}>
          <CuboidCollider args={[8, 0.1, 3]} />
        </RigidBody>
      </Physics>
      <OrbitControls enablePan={false} enableZoom={false} maxPolarAngle={Math.PI / 2.05} minPolarAngle={Math.PI / 3.5} />
    </Canvas>
  );
}
