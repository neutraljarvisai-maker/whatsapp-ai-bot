import React from 'react';
import { motion } from 'framer-motion';

const BatSymbol: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <motion.svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      initial={{ opacity: 0.05 }}
      animate={{ opacity: [0.05, 0.12, 0.05] }}
      transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
    >
      <path d="M12,2C10,2 9,4 9,4C9,4 7,3 5,3C3,3 2,5 2,5C2,5 3,7 3,9C3,11 2,13 2,13C2,13 4,14 6,14C8,14 9,13 10,12C11,13 12,14 12,14C12,14 13,13 14,12C15,13 16,14 18,14C20,14 22,13 22,13C22,13 21,11 21,9C21,7 22,5 22,5C22,5 21,3 19,3C17,3 15,4 15,4C15,4 14,2 12,2Z" />
    </motion.svg>
  );
};

export default BatSymbol;
