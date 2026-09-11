import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "音视频令牌化向量存储系统软件 V1.0",
  description: "本地音视频令牌化与向量入库系统"
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
