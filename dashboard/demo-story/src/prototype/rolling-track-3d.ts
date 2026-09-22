export type MarbleRunVariant = 'coupled' | 'aiBoost';

export interface RampConfig {
  name: string;
  color: string;
  position: [number, number, number];
  tilt: number;
  duration: number;
}

export const RAMP_LENGTH = 2.5;
export const RAMP_WIDTH = 1.8;
export const BALL_RADIUS = 0.22;
export const USER_BUCKET_POSITION: [number, number, number] = [4.8, 0.15, 0];

const coupledRamps: RampConfig[] = [
  { name: 'Product', color: '#62b0ff', position: [-3.2, 1.8, 0], tilt: 0.12, duration: 1.65 },
  { name: 'Design', color: '#b494ff', position: [0, 1.2, 0], tilt: 0.12, duration: 1.65 },
  { name: 'Engineering', color: '#42d477', position: [3.2, 0.6, 0], tilt: 0.12, duration: 1.65 },
];

const boostRamps: RampConfig[] = [
  { name: 'Product', color: '#62b0ff', position: [-3.2, 1.8, 0], tilt: 0.18, duration: 1.35 },
  { name: 'Design', color: '#b494ff', position: [0, 1.2, 0], tilt: 0.27, duration: 1.05 },
  { name: 'Engineering', color: '#42d477', position: [3.2, 0.6, 0], tilt: 0.38, duration: 0.65 },
];

export const rampConfigs: Record<MarbleRunVariant, RampConfig[]> = {
  coupled: coupledRamps,
  aiBoost: boostRamps,
};

export const boosterConfig = {
  position: [2.15, 0.93, 0] as [number, number, number],
  color: '#f3b94f',
  impulseDuration: 0.22,
};

export const totalRunDuration = (variant: MarbleRunVariant) =>
  rampConfigs[variant].reduce((sum, ramp) => sum + ramp.duration, 0) + 0.9;
