import React from 'react';
import { motion } from 'framer-motion';

const CommandConsole: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-32 bg-vecta-panel backdrop-blur-xs border-t border-vecta-cyan/20 flex flex-col p-4 z-10"
    >
      <div className="flex-1 overflow-y-auto mb-2 space-y-2">
        <div className="text-[11px] font-mono text-vecta-cyan bg-black/40 px-2 py-1 inline-block border-l-2 border-vecta-cyan/40">
          <span className="opacity-50 mr-2 font-bold">&gt;</span>
          ACCESSING ENCRYPTED DATA... [SUCCESS]
        </div>
        <br/>
        <div className="text-[11px] font-mono text-vecta-text-primary bg-black/40 px-2 py-1 inline-block">
          <span className="text-vecta-cyan mr-2 font-bold underline">VECTA:</span>
          Awaiting target coordinates or intelligence query.
        </div>
      </div>

      <div className="flex items-center gap-4 bg-black/80 border border-vecta-cyan/20 px-4 py-2 rounded-sm group focus-within:border-vecta-cyan/60 transition-all duration-300">
        <span className="text-xs text-vecta-cyan font-bold tracking-[0.2em] drop-shadow-[0_0_5px_rgba(0,209,255,0.3)]">COMMAND:</span>
        <input
          type="text"
          placeholder="ENTER INSTRUCTION..."
          className="flex-1 bg-transparent border-none outline-none text-sm text-vecta-text-primary placeholder:text-vecta-cyan/30 tracking-wider font-mono uppercase"
        />
      </div>
    </motion.div>
  );
};

export default CommandConsole;
