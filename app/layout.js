import './globals.css';
import Navbar from '../components/Navbar';

export const metadata = {
  title: 'NetSynth IQ',
  description: 'Evaluate structural similarities between real and synthetic network data datasets.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
          {children}
        </main>
      </body>
    </html>
  );
}