import React from 'react';
import { motion } from 'framer-motion';

const AICore: React.FC = () => {
  return (
    <div className="flex-1 relative flex items-center justify-center bg-vecta-bg">
      {/* HUD Background Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,209,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,209,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

      {/* Placeholder Particle Sphere */}
      <div className="relative w-96 h-96 border border-vecta-cyan/20 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(0,209,255,0.05)]">
        <motion.div
          animate={{
            scale: [1, 1.05, 1],
            opacity: [0.3, 0.5, 0.3]
          }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-10 border border-vecta-cyan/40 rounded-full"
        />
        <motion.div
          animate={{
            rotate: 360
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute inset-4 border-t-2 border-vecta-cyan/60 rounded-full"
        />
        <div className="w-4 h-4 bg-vecta-cyan rounded-full shadow-[0_0_20px_#00D1FF]" />
      </div>

      <div className="absolute bottom-10 text-center">
        <div className="text-[10px] tracking-[0.5em] text-vecta-cyan/40 uppercase font-bold">Neural Engine v4.0</div>
      </div>
    </div>
  );
};

export default AICore;
