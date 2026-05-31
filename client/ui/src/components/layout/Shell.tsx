import React from 'react';
import SystemStatus from './SystemStatus';
import ActivityFeed from './ActivityFeed';
import AICore from './AICore';
import CommandConsole from './CommandConsole';
import BatSymbol from '../ui/BatSymbol';

const Shell: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-vecta-bg text-vecta-text-primary font-sans flex flex-col overflow-hidden">
      {/* Background Bat Symbol Watermark */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.08] z-0">
        <BatSymbol className="w-[800px] h-[800px] text-vecta-cyan/20" />
      </div>

      <div className="flex-1 flex overflow-hidden relative z-10">
        <SystemStatus />
        <AICore />
        <ActivityFeed />
      </div>

      <div className="relative z-20">
        <CommandConsole />
      </div>

      {/* HUD Scanlines Effect */}
      <div className="absolute inset-0 pointer-events-none z-[100] opacity-[0.03] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[size:100%_2px,3px_100%] animate-pulse" />
    </div>
  );
};

export default Shell;
