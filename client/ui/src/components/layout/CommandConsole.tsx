import React from 'react';
import { motion } from 'framer-motion';

const CommandConsole: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-32 bg-vecta-panel border-t border-vecta-cyan/30 flex flex-col p-4"
    >
      <div className="flex-1 overflow-y-auto mb-2 space-y-1">
        <div className="text-[11px] font-mono text-vecta-cyan">
          <span className="opacity-50 mr-2">&gt;</span>
          ACCESSING ENCRYPTED DATA... [SUCCESS]
        </div>
        <div className="text-[11px] font-mono text-vecta-text-primary">
          <span className="text-vecta-cyan mr-2">VECTA:</span>
          Awaiting target coordinates or intelligence query.
        </div>
      </div>

      <div className="flex items-center gap-4 bg-black/60 border border-vecta-cyan/20 px-4 py-2 rounded-sm group focus-within:border-vecta-cyan/50 transition-colors">
        <span className="text-xs text-vecta-cyan font-bold tracking-widest">COMMAND:</span>
        <input
          type="text"
          placeholder="ENTER INSTRUCTION..."
          className="flex-1 bg-transparent border-none outline-none text-sm text-vecta-text-primary placeholder:text-vecta-cyan/20 tracking-wider font-mono uppercase"
        />
      </div>
    </motion.div>
  );
};

export default CommandConsole;
