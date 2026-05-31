import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { AICoreState } from '../../hooks/useVectaState';

interface ParticleSphereProps {
  state: AICoreState;
}

const ParticleSphere: React.FC<ParticleSphereProps> = ({ state }) => {
  const points = useRef<THREE.Points>(null!);
  const bgPoints = useRef<THREE.Points>(null!);

  const count = 4000;
  const bgCount = 2000;

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = Math.pow(Math.random(), 0.7) * 2.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  }, []);

  const bgPositions = useMemo(() => {
    const pos = new Float32Array(bgCount * 3);
    for (let i = 0; i < bgCount; i++) {
      const r = 2.5 + Math.random() * 2.0;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  }, []);

  useFrame((threeState) => {
    const time = threeState.clock.getElapsedTime();

    points.current.rotation.y = time * 0.08;
    points.current.rotation.z = time * 0.04;
    bgPoints.current.rotation.y = -time * 0.03;

    let scale = 1;
    let rotationMultiplier = 1;
    let jitter = 0.02;

    switch (state) {
      case 'listening':
        scale = 1.15 + Math.sin(time * 5) * 0.08;
        jitter = 0.05;
        rotationMultiplier = 1.5;
        break;
      case 'thinking':
        rotationMultiplier = 4;
        scale = 0.85 + Math.sin(time * 3) * 0.03;
        jitter = 0.01;
        break;
      case 'speaking':
        scale = 1 + Math.sin(time * 12) * 0.15;
        jitter = 0.1;
        rotationMultiplier = 2;
        break;
      default:
        scale = 1 + Math.sin(time * 0.6) * 0.03;
        jitter = 0.02;
        rotationMultiplier = 1;
        break;
    }

    points.current.scale.setScalar(scale);
    points.current.rotation.y += rotationMultiplier * 0.01;

    const positionsArr = points.current.geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < count; i++) {
        positionsArr[i * 3] += Math.sin(time * 0.5 + i) * jitter * 0.05;
        positionsArr[i * 3 + 1] += Math.cos(time * 0.5 + i) * jitter * 0.05;
        positionsArr[i * 3 + 2] += Math.sin(time * 0.3 + i) * jitter * 0.05;
    }
    points.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <points ref={points}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={count}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.018}
          color="#00D1FF"
          transparent
          opacity={0.9}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
      <points ref={bgPoints}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={bgCount}
            array={bgPositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.012}
          color="#006688"
          transparent
          opacity={0.4}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </>
  );
};

export default ParticleSphere;
