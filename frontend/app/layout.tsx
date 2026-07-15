import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RIOS - Recursive Intelligence Operating System",
  description: "Evolving reasoning system around GPT-OSS-120B via recursive scaffolding, cognitive genome evolution, and PIES evaluation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
