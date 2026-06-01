import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { AICoreState } from '../../hooks/useVectaState';

interface ParticleSphereProps {
  state: AICoreState;
}

const ParticleSphere: React.FC<ParticleSphereProps> = ({ state }) => {
  const pointsRef = useRef<THREE.Points>(null!);
  const outerCloudRef = useRef<THREE.Points>(null!);

  const count = 15000; // High density core
  const outerCount = 5000; // Wispy outer shell

  // Core Cloud Generation (Dense Volumetric)
  const corePositions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      // Box-Muller transform for high-quality Gaussian distribution
      const u1 = Math.random();
      const u2 = Math.random();
      const u3 = Math.random();

      const radius = 0.8 * Math.sqrt(-2.0 * Math.log(u1));
      const theta = 2.0 * Math.PI * u2;
      const phi = Math.acos(2.0 * u3 - 1.0);

      pos[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = radius * Math.cos(phi);
    }
    return pos;
  }, []);

  // Outer Cloud Generation (Sparse & Wispy)
  const outerPositions = useMemo(() => {
    const pos = new Float32Array(outerCount * 3);
    for (let i = 0; i < outerCount; i++) {
      const radius = 1.5 + Math.random() * 2.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      pos[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = radius * Math.cos(phi);
    }
    return pos;
  }, []);

  useFrame((threeState) => {
    const time = threeState.clock.getElapsedTime();

    // Core Motion Logic
    let speed = 0.15;
    let jitter = 0.002;
    let scale = 1.0;
    let intensity = 1.0;

    switch (state) {
      case 'listening':
        speed = 0.4;
        jitter = 0.008;
        scale = 1.05 + Math.sin(time * 8) * 0.03;
        intensity = 1.4;
        break;
      case 'thinking':
        speed = 1.2;
        jitter = 0.001;
        scale = 0.95 + Math.sin(time * 4) * 0.02;
        intensity = 1.8;
        break;
      case 'speaking':
        speed = 0.25;
        jitter = 0.015;
        scale = 1.0 + Math.sin(time * 12) * 0.08;
        intensity = 1.6;
        break;
      default: // idle
        speed = 0.15;
        jitter = 0.002;
        scale = 1.0 + Math.sin(time * 0.5) * 0.02;
        intensity = 1.0;
        break;
    }

    // Apply Global Rotations
    pointsRef.current.rotation.y = time * speed * 0.5;
    pointsRef.current.rotation.z = time * speed * 0.2;
    outerCloudRef.current.rotation.y = -time * speed * 0.2;
    outerCloudRef.current.rotation.x = time * speed * 0.1;

    pointsRef.current.scale.setScalar(scale);

    // Animate Particles (Micro-Turbulence)
    const posAttr = pointsRef.current.geometry.attributes.position;
    const posArr = posAttr.array as Float32Array;

    for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        // Organic swarm movement
        posArr[i3] += Math.sin(time * 0.5 + i) * jitter;
        posArr[i3 + 1] += Math.cos(time * 0.4 + i) * jitter;
        posArr[i3 + 2] += Math.sin(time * 0.3 + i) * jitter;
    }
    posAttr.needsUpdate = true;

    // Dynamic Opacity/Intensity
    const material = pointsRef.current.material as THREE.PointsMaterial;
    material.opacity = (0.4 + Math.sin(time * 2) * 0.05) * intensity;
  });

  return (
    <>
      {/* Dense Core Cloud */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={count}
            array={corePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.012}
          color="#00D1FF"
          transparent
          opacity={0.5}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Wispy Outer Cloud */}
      <points ref={outerCloudRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={outerCount}
            array={outerPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.008}
          color="#004466"
          transparent
          opacity={0.15}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Bright Central Singularity */}
      <mesh>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshBasicMaterial color="#00D1FF" transparent opacity={0.3} blending={THREE.AdditiveBlending} />
      </mesh>
    </>
  );
};

export default ParticleSphere;
