type StatusBannerProps = {
  kind: "error" | "warning";
  message: string;
};

export function StatusBanner({ kind, message }: StatusBannerProps) {
  return <p className={`status-banner ${kind}`}>{message}</p>;
}
