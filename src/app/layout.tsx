import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Ideafrme', description: 'Turn ideas into actionable plans with AI.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
