import React from 'react';
import type { Task } from '../../hooks/useVectaState';

interface ActivityFeedProps {
  tasks: Task[];
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({ tasks }) => {
  return (
    <div className="w-80 h-full bg-vecta-panel/75 backdrop-blur-sm border-l border-vecta-cyan/20 p-6 flex flex-col overflow-hidden z-20">
      <h2 className="text-[10px] tracking-[0.4em] font-black text-vecta-cyan/60 uppercase mb-6 border-b border-vecta-cyan/10 pb-2">
        Daily Task Matrix
      </h2>

      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        {tasks.map(task => (
          <div
            key={task.id}
            className={`p-4 border border-vecta-cyan/10 transition-all duration-300 bg-black/20 ${
              task.status === 'completed' ? 'border-l-2 border-l-vecta-cyan' :
              task.status === 'in-progress' ? 'border-l-2 border-l-vecta-amber' : ''
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 border border-vecta-cyan/30 rounded-sm flex items-center justify-center ${
                task.status === 'completed' ? 'bg-vecta-cyan/20' : ''
              }`}>
                {task.status === 'completed' && <div className="w-1.5 h-1.5 bg-vecta-cyan rounded-full" />}
              </div>
              <div className="flex-1">
                <div className={`text-[10px] font-black tracking-widest uppercase ${
                  task.status === 'completed' ? 'text-vecta-text-secondary line-through' : 'text-vecta-text-primary'
                }`}>
                  {task.name}
                </div>
                <div className="text-[7px] font-mono tracking-widest opacity-40 uppercase mt-1">
                  Status: {task.status.replace('-', ' ')}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-vecta-cyan/5">
         <div className="flex justify-between items-center px-1">
            <span className="text-[9px] text-vecta-text-secondary font-bold uppercase tracking-widest">Core Efficiency</span>
            <span className="text-[9px] text-vecta-cyan font-mono">84.2%</span>
         </div>
         <div className="w-full h-[2px] bg-white/5 mt-2 rounded-full overflow-hidden">
            <div className="h-full bg-vecta-cyan/50 w-[84%]" />
         </div>
      </div>
    </div>
  );
};

export default ActivityFeed;
