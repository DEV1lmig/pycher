import './globals.css';
import type { Metadata } from 'next';
import { Inter, Gelasio } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const gelasio = Gelasio({ subsets: ['latin'], weight: ['400', '700'], variable: '--font-gelasio' });

export const metadata: Metadata = {
  title: 'PyCher - Python Learning Platform',
  description: 'Learn Python programming with structured courses and interactive lessons',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${gelasio.variable} font-sans`}>{children}</body>
    </html>
  );
}
