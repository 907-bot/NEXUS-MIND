import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "NexusMind - Autonomous AI Network",
  description: "Next-generation multi-agent swarm intelligence",
  icons: {
    icon: "favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <html lang="en" className="dark">
        <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen antialiased`}>
          {children}
        </body>
      </html>
    </Providers>
  );
}
