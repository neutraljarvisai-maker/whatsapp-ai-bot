import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const AICore = ({ state = 'IDLE', volume = 0 }) => {
  const points = useRef();
  const particleCount = 10000;

  const [positions, step] = useMemo(() => {
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const phi = Math.acos(-1 + (2 * i) / particleCount);
      const theta = Math.sqrt(particleCount * Math.PI) * phi;
      positions[i * 3] = Math.cos(theta) * Math.sin(phi);
      positions[i * 3 + 1] = Math.sin(theta) * Math.sin(phi);
      positions[i * 3 + 2] = Math.cos(phi);
    }
    return [positions, 0];
  }, []);

  useFrame((state_frame) => {
    const time = state_frame.clock.getElapsedTime();
    const scale = state === 'LISTENING' ? 1.2 + volume : 1.0 + Math.sin(time) * 0.05;
    points.current.scale.set(scale, scale, scale);
    points.current.rotation.y += 0.002;
    points.current.rotation.z += 0.001;
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.015}
        color="#00d4ff"
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
};

export default AICore;
