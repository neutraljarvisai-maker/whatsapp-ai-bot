import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Float } from '@react-three/drei';
import ParticleSphere from '../three/ParticleSphere';

interface MainPanelProps {
  children?: React.ReactNode;
}

const MainPanel: React.FC<MainPanelProps> = ({ children }) => {
  return (
    <div className="flex-1 relative flex flex-col items-center justify-center overflow-hidden">
      {/* Decorative corners */}
      <div className="absolute top-6 left-6 w-12 h-12 border-t-2 border-l-2 border-vecta-cyan/20 rounded-tl-lg" />
      <div className="absolute top-6 right-6 w-12 h-12 border-t-2 border-r-2 border-vecta-cyan/20 rounded-tr-lg" />
      <div className="absolute bottom-6 left-6 w-12 h-12 border-b-2 border-l-2 border-vecta-cyan/20 rounded-bl-lg" />
      <div className="absolute bottom-6 right-6 w-12 h-12 border-b-2 border-r-2 border-vecta-cyan/20 rounded-br-lg" />

      {/* HUD Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,212,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,212,255,0.03)_1px,transparent_1px)] bg-[size:60px_60px] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,212,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(0,212,255,0.01)_1px,transparent_1px)] bg-[size:15px_15px] pointer-events-none" />

      {/* Main Content Area (3D Sphere) */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
          <color attach="background" args={['#000']} />
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <Suspense fallback={null}>
            <Float speed={2.5} rotationIntensity={0.8} floatIntensity={0.8}>
              <ParticleSphere />
            </Float>
          </Suspense>
          <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
        </Canvas>
      </div>

      {/* UI Content Layer */}
      <div className="z-10 w-full h-full flex items-center justify-center pointer-events-none">
        <div className="pointer-events-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

export default MainPanel;
