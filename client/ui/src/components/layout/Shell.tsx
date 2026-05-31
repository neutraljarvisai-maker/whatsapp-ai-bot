import React from 'react';
import SystemStatus from './SystemStatus';
import ActivityFeed from './ActivityFeed';
import AICore from './AICore';
import CommandConsole from './CommandConsole';
import BatSymbol from '../ui/BatSymbol';

const Shell: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-vecta-bg text-vecta-text-primary font-sans flex flex-col overflow-hidden select-none">
      {/* Background Bat Symbol Watermark - Very subtle, no overlap with content */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.05] z-0">
        <BatSymbol className="w-[800px] h-[800px] text-vecta-cyan/10" />
      </div>

      <div className="flex-1 flex overflow-hidden relative z-10">
        <SystemStatus />
        <AICore />
        <ActivityFeed />
      </div>

      <div className="relative z-20">
        <CommandConsole />
      </div>

      {/* HUD Static Effect - Non-flashy, very subtle scanlines */}
      <div className="absolute inset-0 pointer-events-none z-[100] opacity-[0.02] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[size:100%_2px]" />

      {/* Corner Brackets for Cinematic Feel */}
      <div className="absolute top-4 left-4 w-8 h-8 border-t border-l border-vecta-cyan/30 pointer-events-none" />
      <div className="absolute top-4 right-4 w-8 h-8 border-t border-r border-vecta-cyan/30 pointer-events-none" />
      <div className="absolute bottom-4 left-4 w-8 h-8 border-b border-l border-vecta-cyan/30 pointer-events-none" />
      <div className="absolute bottom-4 right-4 w-8 h-8 border-b border-r border-vecta-cyan/30 pointer-events-none" />
    </div>
  );
};

export default Shell;
