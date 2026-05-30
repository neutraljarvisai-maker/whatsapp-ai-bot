import React, { useState, useEffect } from 'react';
import AICore from './components/AICore';
import { Canvas } from '@react-three/fiber';
import { motion } from 'framer-motion';

const App = () => {
  const [status, setStatus] = useState('IDLE');
  const [logs, setLogs] = useState([]);

  return (
    <div className="bg-[#050505] text-[#00d4ff] h-screen w-screen overflow-hidden flex flex-col font-mono relative">
      <div className="HUD-GRID absolute inset-0 pointer-events-none opacity-10"
           style={{ backgroundImage: 'linear-gradient(#005577 1px, transparent 1px), linear-gradient(90deg, #005577 1px, transparent 1px)', backgroundSize: '50px 50px' }}></div>

      {/* Header */}
      <header className="p-4 border-b border-[#005577] flex justify-between bg-[#00557711] backdrop-blur-sm z-10">
        <span className="tracking-[0.5em] font-bold">VECTA CLOUD OS v3.0 // NEURAL LINK</span>
        <span>{new Date().toLocaleTimeString()}</span>
      </header>

      {/* Main OS View */}
      <main className="flex-grow flex items-center justify-center relative">
        <div className="absolute inset-0 z-0">
          <Canvas camera={{ position: [0, 0, 5] }}>
            <AICore state={status} />
          </Canvas>
        </div>

        {/* Cinematic HUD Overlays */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="z-10 w-full h-full flex justify-between p-10 pointer-events-none">
          <div className="LEFT-PANEL w-64 border border-[#00557733] p-4 bg-[#000000aa] backdrop-blur-md self-start pointer-events-auto">
            <h3 className="text-xs border-b border-[#00d4ff55] mb-2 pb-1">SYSTEM ANALYTICS</h3>
            <div className="space-y-2 text-[10px]">
              <div className="flex justify-between"><span>CORE LOAD:</span><span>{Math.random().toFixed(2)}%</span></div>
              <div className="flex justify-between"><span>MEM SWAP:</span><span>STABLE</span></div>
              <div className="flex justify-between"><span>NET LINK:</span><span>SECURE</span></div>
            </div>
          </div>

          <div className="RIGHT-PANEL w-64 border border-[#00557733] p-4 bg-[#000000aa] backdrop-blur-md self-end pointer-events-auto">
            <h3 className="text-xs border-b border-[#00d4ff55] mb-2 pb-1">ACTIVITY TRACE</h3>
            <div className="h-64 overflow-y-auto space-y-1 text-[9px] text-[#0088aa]">
              {logs.map((log, i) => <div key={i}>> {log}</div>)}
            </div>
          </div>
        </motion.div>
      </main>

      {/* Console */}
      <footer className="p-4 border-t border-[#005577] bg-[#000000ee] z-10">
        <input
          type="text"
          className="w-full bg-transparent border-none outline-none text-[#00d4ff] placeholder-[#005577]"
          placeholder="AWAITING NEURAL INPUT..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              setLogs([...logs, e.target.value]);
              e.target.value = '';
            }
          }}
        />
      </footer>
    </div>
  );
};

export default App;
