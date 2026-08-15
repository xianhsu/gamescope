import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** shadcn-style class combiner. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** 友好的绝对日期，例如 "2026年8月15日"。 */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "未知日期";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "未知日期";
  return d.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

/** 相对时间，例如 "3 小时前"、"2 天前"。 */
export function relativeTime(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const diffMs = Date.now() - d.getTime();
  const sec = Math.round(diffMs / 1000);
  const min = Math.round(sec / 60);
  const hr = Math.round(min / 60);
  const day = Math.round(hr / 24);
  if (sec < 60) return "刚刚";
  if (min < 60) return `${min} 分钟前`;
  if (hr < 24) return `${hr} 小时前`;
  if (day < 30) return `${day} 天前`;
  return formatDate(value);
}

/** Title-case a slug/enum, e.g. "the-legend-of-zelda" → "The Legend Of Zelda". */
export function humanize(value: string): string {
  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** 文章分类的中文标签。 */
const CATEGORY_LABELS: Record<string, string> = {
  official: "官方",
  media: "媒体",
  rumor: "传闻",
  update: "更新",
  review: "评测",
  deal: "优惠",
};

export function categoryLabel(value: string): string {
  return CATEGORY_LABELS[value?.toLowerCase()] ?? humanize(value);
}
