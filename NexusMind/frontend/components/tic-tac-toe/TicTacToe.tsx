'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, Trophy, User, Monitor } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type Player = 'X' | 'O' | null;

export default function TicTacToe() {
  const [board, setBoard] = useState<Player[]>(Array(9).fill(null));
  const [isXNext, setIsXNext] = useState(true);
  const [winner, setWinner] = useState<Player | 'Draw'>(null);
  const [winningLine, setWinningLine] = useState<number[] | null>(null);
  const [gameMode, setGameMode] = useState<'PvP' | 'PvE'>('PvE');

  const calculateWinner = (squares: Player[]) => {
    const lines = [
      [0, 1, 2],
      [3, 4, 5],
      [6, 7, 8],
      [0, 3, 6],
      [1, 4, 7],
      [2, 5, 8],
      [0, 4, 8],
      [2, 4, 6],
    ];
    for (let i = 0; i < lines.length; i++) {
      const [a, b, c] = lines[i];
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return { winner: squares[a], line: lines[i] };
      }
    }
    if (squares.every((square) => square !== null)) {
      return { winner: 'Draw' as const, line: null };
    }
    return null;
  };

  const handleClick = (i: number) => {
    if (winner || board[i]) return;

    const newBoard = [...board];
    newBoard[i] = isXNext ? 'X' : 'O';
    setBoard(newBoard);
    setIsXNext(!isXNext);

    const result = calculateWinner(newBoard);
    if (result) {
      setWinner(result.winner);
      setWinningLine(result.line);
    }
  };

  const resetGame = () => {
    setBoard(Array(9).fill(null));
    setIsXNext(true);
    setWinner(null);
    setWinningLine(null);
  };

  // Simple AI move
  useEffect(() => {
    if (gameMode === 'PvE' && !isXNext && !winner) {
      const timer = setTimeout(() => {
        const availableMoves = board
          .map((val, idx) => (val === null ? idx : null))
          .filter((val) => val !== null) as number[];
        
        if (availableMoves.length > 0) {
          // Priority 1: Check if AI can win
          for (const move of availableMoves) {
            const boardCopy = [...board];
            boardCopy[move] = 'O';
            if (calculateWinner(boardCopy)?.winner === 'O') {
              handleClick(move);
              return;
            }
          }

          // Priority 2: Check if AI needs to block player
          for (const move of availableMoves) {
            const boardCopy = [...board];
            boardCopy[move] = 'X';
            if (calculateWinner(boardCopy)?.winner === 'X') {
              handleClick(move);
              return;
            }
          }

          // Priority 3: Random move
          const randomMove = availableMoves[Math.floor(Math.random() * availableMoves.length)];
          handleClick(randomMove);
        }
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [isXNext, board, winner, gameMode]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[600px] p-8 font-sans">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl overflow-hidden relative"
      >
        {/* Background Gradients */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
          <div className="absolute top-[-10%] right-[-10%] w-1/2 h-1/2 bg-blue-500/10 blur-[80px] rounded-full" />
          <div className="absolute bottom-[-10%] left-[-10%] w-1/2 h-1/2 bg-purple-500/10 blur-[80px] rounded-full" />
        </div>

        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Tic-Tac-Toe
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => setGameMode(gameMode === 'PvP' ? 'PvE' : 'PvP')}
              className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-white/70"
              title={`Switch to ${gameMode === 'PvP' ? 'PvE' : 'PvP'}`}
            >
              {gameMode === 'PvP' ? <User size={20} /> : <Monitor size={20} />}
            </button>
            <button
              onClick={resetGame}
              className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-white/70"
              title="Reset Game"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        </div>

        <div className="mb-6 text-center">
          <AnimatePresence mode="wait">
            {winner ? (
              <motion.div
                key="winner"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="flex items-center justify-center gap-2 text-xl font-semibold text-yellow-400"
              >
                <Trophy size={24} />
                {winner === 'Draw' ? "It's a Draw!" : `${winner} Wins!`}
              </motion.div>
            ) : (
              <motion.div
                key="turn"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-lg font-medium text-white/60"
              >
                {isXNext ? "X's Turn" : "O's Turn"}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="grid grid-cols-3 gap-3 aspect-square">
          {board.map((square, i) => (
            <motion.button
              key={i}
              whileHover={!winner && !square ? { scale: 1.02, backgroundColor: 'rgba(255, 255, 255, 0.08)' } : {}}
              whileTap={!winner && !square ? { scale: 0.95 } : {}}
              onClick={() => handleClick(i)}
              className={cn(
                "relative flex items-center justify-center text-4xl font-bold rounded-2xl transition-all duration-300",
                "bg-white/5 border border-white/10 shadow-lg backdrop-blur-sm",
                winningLine?.includes(i) ? "bg-yellow-400/20 border-yellow-400/50" : "",
                !square && !winner ? "cursor-pointer" : "cursor-default"
              )}
            >
              <AnimatePresence>
                {square && (
                  <motion.span
                    initial={{ scale: 0.5, opacity: 0, rotate: -45 }}
                    animate={{ scale: 1, opacity: 1, rotate: 0 }}
                    className={cn(
                      square === 'X' ? "text-blue-400 drop-shadow-[0_0_8px_rgba(96,165,250,0.5)]" : "text-pink-400 drop-shadow-[0_0_8px_rgba(244,114,182,0.5)]"
                    )}
                  >
                    {square}
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          ))}
        </div>

        <div className="mt-8 flex justify-between text-sm text-white/40">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span> Player X
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-pink-400"></span> {gameMode === 'PvP' ? 'Player O' : 'AI Bot'}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
