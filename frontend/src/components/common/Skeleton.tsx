import { Loader2 } from "lucide-react";

interface SkeletonProps {
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  className?: string;
}

export function Skeleton({ variant = "rectangular", width, height, className = "" }: SkeletonProps) {
  const style: React.CSSProperties = {
    width: width ?? (variant === "circular" ? 40 : "100%"),
    height: height ?? (variant === "text" ? 16 : 60),
    borderRadius: variant === "circular" ? "50%" : "8px",
  };

  return (
    <div
      className={`animate-pulse ${className}`}
      style={{
        ...style,
        background: "var(--bg-elevated)",
      }}
    />
  );
}

export function MessageSkeleton() {
  return (
    <div className="flex gap-3 px-5 py-3">
      <Skeleton variant="circular" width={32} height={32} />
      <div className="flex-1 space-y-2">
        <Skeleton variant="text" width="30%" height={12} />
        <Skeleton variant="rectangular" width="85%" height={48} />
      </div>
    </div>
  );
}

export function ChatLoadingSkeleton() {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <div className="flex gap-3">
        <Skeleton variant="circular" width={32} height={32} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="20%" height={12} />
          <Skeleton variant="rectangular" width="70%" height={60} />
        </div>
      </div>
      <div className="flex gap-3 justify-end">
        <div className="space-y-2 items-end">
          <Skeleton variant="text" width="15%" height={12} />
          <Skeleton variant="rectangular" width="50%" height={48} />
        </div>
      </div>
      <div className="flex gap-3">
        <Skeleton variant="circular" width={32} height={32} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="25%" height={12} />
          <Skeleton variant="rectangular" width="90%" height={80} />
        </div>
      </div>
    </div>
  );
}

export function FullPageSkeleton() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin mx-auto" style={{ color: "var(--accent)" }} />
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Loading...
        </p>
      </div>
    </div>
  );
}
