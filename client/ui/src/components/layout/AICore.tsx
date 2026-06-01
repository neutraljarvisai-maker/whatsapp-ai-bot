import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import ParticleSphere from '../three/ParticleSphere';
import type { AICoreState } from '../../hooks/useVectaState';
import BatSymbol from '../ui/BatSymbol';

interface AICoreProps {
  state: AICoreState;
}

const AICore: React.FC<AICoreProps> = ({ state }) => {
  return (
    <div className="flex-1 relative flex items-center justify-center bg-transparent overflow-hidden">
      {/* HUD Background Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,209,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,209,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px] pointer-events-none" />

      {/* Bat Symbol Background Emblem */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
        <BatSymbol className="w-[500px] h-[500px] text-[#00D1FF] opacity-[0.03]" />
      </div>

      <div className="w-full h-full relative z-10">
        <Canvas
          camera={{ position: [0, 0, 5], fov: 45 }}
          gl={{
            antialias: false,
            powerPreference: "high-performance",
            alpha: true,
          }}
        >
          <ambientLight intensity={0.5} />

          <Suspense fallback={null}>
            <ParticleSphere state={state} />

            <EffectComposer enableNormalPass={false}>
              <Bloom
                luminanceThreshold={0}
                mipmapBlur
                luminanceSmoothing={0.9}
                intensity={1.5}
                radius={0.4}
              />
            </EffectComposer>
          </Suspense>
        </Canvas>
      </div>

      <div className="absolute bottom-12 text-center pointer-events-none select-none">
        <div className="text-[10px] tracking-[0.8em] text-vecta-cyan/30 uppercase font-bold drop-shadow-[0_0_10px_rgba(0,209,255,0.2)]">
          Neural Core v4.2 // {state.toUpperCase()}
        </div>
      </div>
    </div>
  );
};

export default AICore;
