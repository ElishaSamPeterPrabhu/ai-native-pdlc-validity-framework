import {  ModusWcButton } from '@trimble-oss/moduswebcomponents-react';

interface LegendBarProps {
  activeBeat: number;
  onJump: (index: number) => void;
  reducedMotion: boolean;
  onToggleMotion: () => void;
}

const beats = ['Coupled system', 'AI catalyst', 'Engineering pressure', 'Expanded loop', 'Engineering loop'];

export function LegendBar({ activeBeat, onJump, reducedMotion, onToggleMotion }: LegendBarProps) {
  return (
    <aside className="legend-bar" aria-label="Demo story navigation and legend">
      <div className="legend-beats">
        {beats.map((beat, index) => (
          <ModusWcButton
            key={beat}
            color={index === activeBeat ? 'primary' : 'tertiary'}
            variant={index === activeBeat ? 'filled' : 'outlined'}
            size="sm"
            fullWidth={true}
            className={`beat-marker ${index === activeBeat ? 'is-active' : ''}`}
            onButtonClick={() => onJump(index)}
            aria-label={`Go to ${beat}`}
          >
            <span>{String(index + 1).padStart(2, '0')}</span>
            {beat}
          </ModusWcButton>
        ))}
      </div>
    </aside>
  );
}
