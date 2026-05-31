import React from 'react';
import type { AICoreState } from '../../hooks/useVectaState';

interface CommandConsoleProps {
  state: AICoreState;
}

const CommandConsole: React.FC<CommandConsoleProps> = ({ state }) => {
  return (
    <div className="h-44 bg-vecta-panel/75 backdrop-blur-sm border-t border-vecta-cyan/20 flex flex-col p-6 gap-4 z-30">
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        <div className="flex items-start gap-3">
          <span className="text-vecta-cyan font-black text-[10px] mt-0.5">&gt;</span>
          <div className="text-[11px] font-mono text-vecta-cyan/60 tracking-wider uppercase">
            Neural Uplink Verified. Core: {state}
          </div>
        </div>
        <div className="flex items-start gap-3">
          <span className="text-vecta-cyan font-black text-[10px] mt-0.5">VECTA:</span>
          <div className="text-[11px] font-mono text-vecta-text-primary tracking-wide leading-relaxed bg-vecta-cyan/5 p-3 border-l border-vecta-cyan/20 rounded-r-sm max-w-3xl">
            All tactical systems are operational. I am ready to process your next directive, Master Bruce.
          </div>
        </div>
      </div>

      <div className="relative group max-w-4xl">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <span className="text-[10px] text-vecta-cyan font-black tracking-[0.3em] drop-shadow-[0_0_5px_rgba(0,209,255,0.4)] uppercase">Execute:</span>
        </div>
        <input
          type="text"
          placeholder="ENTER DIRECTIVE..."
          className="w-full bg-black/40 border border-vecta-cyan/10 pl-28 pr-4 py-3 text-sm text-vecta-text-primary placeholder:text-vecta-cyan/20 tracking-[0.1em] font-mono uppercase focus:outline-none focus:border-vecta-cyan/40 transition-all duration-300 rounded-sm"
        />
      </div>
    </div>
  );
};

export default CommandConsole;
