import { useState, useEffect, useCallback } from 'react';

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

export interface Message {
  id: string;
  sender: 'user' | 'vecta';
  text: string;
  timestamp: Date;
}

export interface VectaState {
  systemStats: SystemStats;
  aiCoreState: AICoreState;
  dailyTasks: Task[];
  systemTime: Date;
  consoleMessages: Message[];
}

export const useVectaState = () => {
  const [state, setState] = useState<VectaState>({
    systemStats: {
      cpu: 13.0,
      gpu: 7.4,
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
    consoleMessages: [
      {
        id: '0',
        sender: 'vecta',
        text: 'All tactical systems are operational. I am ready to process your next directive, Master Bruce.',
        timestamp: new Date(),
      }
    ],
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setState(prev => ({
        ...prev,
        systemTime: new Date(),
        systemStats: {
          ...prev.systemStats,
          cpu: Math.max(8, Math.min(95, prev.systemStats.cpu + (Math.random() - 0.5) * 1.2)),
          gpu: Math.max(4, Math.min(98, prev.systemStats.gpu + (Math.random() - 0.5) * 0.8)),
        }
      }));
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const setAICoreState = useCallback((newState: AICoreState) => {
    setState(prev => ({ ...prev, aiCoreState: newState }));
  }, []);

  const addConsoleMessage = useCallback((text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date(),
    };

    // Add user message immediately
    setState(prev => ({
      ...prev,
      consoleMessages: [...prev.consoleMessages, userMessage],
    }));

    // Trigger AI response flow
    setAICoreState('thinking');

    setTimeout(() => {
      const response: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'vecta',
        text: `Processing directive: "${text}". Neural uplink verified. Command accepted.`,
        timestamp: new Date(),
      };

      setState(prev => ({
        ...prev,
        aiCoreState: 'idle',
        consoleMessages: [...prev.consoleMessages, response],
      }));
    }, 1200);
  }, [setAICoreState]);

  return { state, setAICoreState, addConsoleMessage };
};
