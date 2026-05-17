import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Slide Analysis System Demo",
  description: "Manager demo dashboard for the Slide Analysis System MVP"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
