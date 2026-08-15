import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/site-footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: {
    default: "GameScope — AI 游戏资讯情报平台",
    template: "%s · GameScope",
  },
  description:
    "GameScope 聚合游戏资讯，并通过基于混合检索流水线的、带引用来源的可信 AI 搜索来回答你的问题。",
  metadataBase: new URL("http://localhost:3000"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={inter.variable}>
      <body className="min-h-screen font-sans antialiased">
        <SiteHeader />
        <main className="min-h-[calc(100vh-3.5rem)]">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
