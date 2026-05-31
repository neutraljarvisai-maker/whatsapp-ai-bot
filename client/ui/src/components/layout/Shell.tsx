import React from 'react';
import SystemStatus from './SystemStatus';
import ActivityFeed from './ActivityFeed';
import AICore from './AICore';
import CommandConsole from './CommandConsole';
import TopBar from './TopBar';
import { useVectaState } from '../../hooks/useVectaState';

const Shell: React.FC = () => {
  const { state } = useVectaState();

  return (
    <div className="fixed inset-0 bg-black text-vecta-text-primary font-sans flex flex-col overflow-hidden select-none">
      <TopBar time={state.systemTime} />

      <div className="flex-1 flex overflow-hidden relative">
        <SystemStatus stats={state.systemStats} />
        <AICore state={state.aiCoreState} />
        <ActivityFeed tasks={state.dailyTasks} />
      </div>

      <CommandConsole state={state.aiCoreState} />

      {/* Cinematic HUD Overlays */}
      <div className="absolute inset-0 pointer-events-none z-[100] opacity-[0.02] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[size:100%_2px]" />

      {/* Corner Brackets */}
      <div className="absolute top-16 left-6 w-12 h-12 border-t border-l border-vecta-cyan/20 pointer-events-none" />
      <div className="absolute top-16 right-6 w-12 h-12 border-t border-r border-vecta-cyan/20 pointer-events-none" />
      <div className="absolute bottom-[180px] left-6 w-12 h-12 border-b border-l border-vecta-cyan/20 pointer-events-none" />
      <div className="absolute bottom-[180px] right-6 w-12 h-12 border-b border-r border-vecta-cyan/20 pointer-events-none" />
    </div>
  );
};

export default Shell;
