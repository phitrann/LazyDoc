import { Suspense } from "react";

import { ReportClient } from "./ReportClient";

export default function ReportPage() {
  return (
    <Suspense fallback={<div className="report-content report-loading">Loading report...</div>}>
      <ReportClient />
    </Suspense>
  );
}
