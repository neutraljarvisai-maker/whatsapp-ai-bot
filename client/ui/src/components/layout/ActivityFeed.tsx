import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface Log {
  id: string;
  timestamp: string;
  message: string;
}

const ActivityFeed: React.FC = () => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const logs: Log[] = [
    { id: '1', timestamp: '22:45:12', message: 'Encryption protocol initialized.' },
    { id: '2', timestamp: '22:45:15', message: 'Scanning perimeter sensors...' },
    { id: '3', timestamp: '22:45:18', message: 'Neural link established.' },
    { id: '4', timestamp: '22:45:20', message: 'Uplink to Batcomputer confirmed.' },
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-80 h-full bg-vecta-panel backdrop-blur-xs border-l border-vecta-cyan/20 p-6 flex flex-col z-10"
    >
      <h2 className="text-xs tracking-[0.3em] font-bold text-vecta-cyan uppercase mb-4 drop-shadow-sm">Activity Stream</h2>
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin"
      >
        {logs.map(log => (
          <div key={log.id} className="text-[11px] leading-relaxed bg-black/30 p-2 border-l border-vecta-cyan/10">
            <span className="text-vecta-cyan/60 font-mono mr-2 font-bold">[{log.timestamp}]</span>
            <span className="text-vecta-text-primary/90 font-medium">{log.message}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

export default ActivityFeed;
