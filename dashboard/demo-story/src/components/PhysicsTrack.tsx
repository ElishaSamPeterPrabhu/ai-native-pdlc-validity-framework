import { RollingTrack } from './RollingTrack';
import { RollingTrack3DPhysicsBoostScene } from '../prototype/RollingTrack3DPhysicsBoostScene';
import { RollingTrack3DPhysicsScene } from '../prototype/RollingTrack3DPhysicsScene';

interface PhysicsTrackProps {
  variant: 'coupled' | 'aiBoost';
  reducedMotion: boolean;
}

const usePhysicsTrack = import.meta.env.VITE_USE_PHYSICS_TRACK !== 'false';

export function PhysicsTrack({ variant, reducedMotion }: PhysicsTrackProps) {
  if (!usePhysicsTrack) {
    return <RollingTrack variant={variant} reducedMotion={reducedMotion} />;
  }

  return (
    <div className="official-physics-track">
      {variant === 'coupled' ? <RollingTrack3DPhysicsScene /> : <RollingTrack3DPhysicsBoostScene />}
    </div>
  );
}
