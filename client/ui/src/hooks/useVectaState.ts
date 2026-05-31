import { useState, useEffect } from 'react';

export type AICoreState = 'idle' | 'listening' | 'thinking' | 'speaking';

export interface SystemStats {
  cpu: number;
  gpu: number;
  ram: number;
  network: string;
  vision: boolean;
  voice: boolean;
}

export interface Task {
  id: string;
  name: string;
  status: 'pending' | 'in-progress' | 'completed';
}

export interface VectaState {
  systemStats: SystemStats;
  aiCoreState: AICoreState;
  dailyTasks: Task[];
  systemTime: Date;
}

export const useVectaState = () => {
  const [state, setState] = useState<VectaState>({
    systemStats: {
      cpu: 12,
      gpu: 8,
      ram: 4.2,
      network: '128 MBPS',
      vision: true,
      voice: true,
    },
    aiCoreState: 'idle',
    dailyTasks: [
      { id: '1', name: 'Initialize Encryption Protocol', status: 'completed' },
      { id: '2', name: 'Scan Perimeter Sensors', status: 'in-progress' },
      { id: '3', name: 'Analyze Satellite Feed', status: 'pending' },
      { id: '4', name: 'Neural Link Calibration', status: 'pending' },
    ],
    systemTime: new Date(),
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setState(prev => ({
        ...prev,
        systemTime: new Date(),
        // Simulate minor fluctuations
        systemStats: {
          ...prev.systemStats,
          cpu: Math.max(5, Math.min(95, prev.systemStats.cpu + (Math.random() - 0.5) * 2)),
          gpu: Math.max(2, Math.min(98, prev.systemStats.gpu + (Math.random() - 0.5) * 1)),
        }
      }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const setAICoreState = (newState: AICoreState) => {
    setState(prev => ({ ...prev, aiCoreState: newState }));
  };

  return { state, setAICoreState };
};
