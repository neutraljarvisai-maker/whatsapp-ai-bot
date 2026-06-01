import React, { useState, useRef, useEffect } from 'react';
import type { Message } from '../../hooks/useVectaState';

interface CommandConsoleProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
}

const CommandConsole: React.FC<CommandConsoleProps> = ({ messages, onSendMessage }) => {
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed) {
      onSendMessage(trimmed);
      setInputValue('');
    }
  };

  return (
    <div className="h-44 bg-vecta-panel/75 backdrop-blur-sm border-t border-vecta-cyan/20 flex flex-col p-6 gap-4 z-30">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 custom-scrollbar"
      >
        {messages.map((msg) => (
          <div key={msg.id} className="flex items-start gap-3 animate-in fade-in slide-in-from-left-1 duration-300">
            <span className={`font-black text-[10px] mt-0.5 tracking-tighter ${msg.sender === 'vecta' ? 'text-vecta-cyan' : 'text-vecta-amber'}`}>
              {msg.sender === 'vecta' ? 'VECTA:' : 'USER:'}
            </span>
            <div className={`text-[11px] font-mono tracking-wide leading-relaxed p-2 border-l border-vecta-cyan/10 rounded-r-sm max-w-4xl ${
              msg.sender === 'vecta' ? 'text-vecta-text-primary bg-vecta-cyan/5' : 'text-vecta-cyan/80 bg-white/5'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="relative group max-w-5xl">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <span className="text-[10px] text-vecta-cyan font-black tracking-[0.3em] drop-shadow-[0_0_5px_rgba(0,209,255,0.4)] uppercase">Execute:</span>
        </div>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="ENTER DIRECTIVE..."
          autoFocus
          className="w-full bg-black/40 border border-vecta-cyan/10 pl-28 pr-4 py-3 text-sm text-vecta-text-primary placeholder:text-vecta-cyan/20 tracking-[0.1em] font-mono uppercase focus:outline-none focus:border-vecta-cyan/40 transition-all duration-300 rounded-sm"
        />
      </form>
    </div>
  );
};

export default CommandConsole;
