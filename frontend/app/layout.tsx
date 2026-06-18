import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AV-TokenVault",
  description: "本地音视频 Token 化与向量入库原型系统"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
