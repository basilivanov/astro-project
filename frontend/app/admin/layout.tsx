import { Suspense } from "react";

import { AdminNav } from "../../components/AdminNav";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row font-sans">
      <Suspense fallback={<div className="hidden md:block md:w-64 border-r border-slate-100 bg-white" />}>
        <AdminNav />
      </Suspense>
      <div className="flex-1 min-h-screen md:ml-64 pb-20 md:pb-0">
        <div className="max-w-7xl mx-auto px-4 md:px-8">
            {children}
        </div>
      </div>
    </div>
  );
}
