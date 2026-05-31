import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import StatusBar from './StatusBar';
import Sidebar from './Sidebar';
import MainPanel from './MainPanel';

interface ShellProps {
  children?: React.ReactNode;
  status?: 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';
}

const Shell: React.FC<ShellProps> = ({ children, status = 'IDLE' }) => {
  return (
    <div className="fixed inset-0 bg-black text-vecta-cyan font-mono flex flex-col overflow-hidden select-none">
      {/* Cinematic Overlays */}
      <div className="absolute inset-0 pointer-events-none z-[100] opacity-[0.03] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[size:100%_2px,3px_100%] animate-pulse" />

      {/* Vignette */}
      <div className="absolute inset-0 pointer-events-none z-[90] shadow-[inset_0_0_150px_rgba(0,0,0,0.8)]" />

      <StatusBar status={status} />

      <div className="flex-1 flex overflow-hidden">
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex"
        >
          <Sidebar />
        </motion.div>

        <MainPanel>
          <AnimatePresence mode="wait">
            <motion.div
              key={status}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.05, opacity: 0 }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
              className="w-full h-full flex items-center justify-center"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </MainPanel>
      </div>

      {/* Footer / Input Area */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="h-16 border-t border-vecta-cyan/20 bg-vecta-bg-matte flex items-center px-6 gap-4 z-10"
      >
        <div className="text-vecta-cyan/40 text-[10px] tracking-[0.4em] uppercase font-bold">Instruction:</div>
        <input
          type="text"
          placeholder="AWAITING COMMAND..."
          className="flex-1 bg-transparent border-none outline-none text-vecta-cyan placeholder:text-vecta-cyan/10 tracking-[0.2em] text-sm uppercase font-bold"
        />
        <div className="flex gap-1">
          {[1, 2, 3].map(i => (
            <div key={i} className="w-1 h-3 bg-vecta-cyan/20 rounded-full" />
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Shell;
