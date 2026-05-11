import TicTacToe from '@/components/tic-tac-toe/TicTacToe';

export const metadata = {
  title: 'Tic-Tac-Toe | NexusMind',
  description: 'A premium Tic-Tac-Toe game built with Next.js and Framer Motion.',
};

export default function TicTacToePage() {
  return (
    <main className="min-h-screen bg-[#030712] flex items-center justify-center">
      <TicTacToe />
    </main>
  );
}
