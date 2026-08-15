import { AlertTriangle, Inbox, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  title = "这里还没有内容",
  description = "当前视图暂无数据可显示。",
  icon,
  className,
  action,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed bg-muted/30 px-6 py-14 text-center",
        className,
      )}
    >
      <div className="mb-3 text-muted-foreground">{icon ?? <Inbox className="h-8 w-8" />}</div>
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message?: string;
  requestId?: string | null;
  isNetwork?: boolean;
  className?: string;
  action?: React.ReactNode;
}

export function ErrorState({
  title = "出错了",
  message = "请求无法完成。",
  requestId,
  isNetwork,
  className,
  action,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-amber-200 bg-amber-50 px-6 py-12 text-center",
        className,
      )}
    >
      <div className="mb-3 text-amber-600">
        {isNetwork ? <WifiOff className="h-8 w-8" /> : <AlertTriangle className="h-8 w-8" />}
      </div>
      <p className="text-sm font-semibold text-amber-900">{title}</p>
      <p className="mt-1 max-w-md text-sm text-amber-800">{message}</p>
      {requestId ? (
        <p className="mt-2 font-mono text-xs text-amber-700/80">请求 ID：{requestId}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
