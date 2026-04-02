import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const backendUrl = process.env.INTERNAL_API_URL || "http://backend:8000";
  
  try {
    const res = await fetch(`${backendUrl}/health`, {
      cache: 'no-store',
    });
    
    if (!res.ok) {
      return NextResponse.json(
        { status: "error", db: `Backend returned ${res.status}` },
        { status: res.status }
      );
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Health proxy error:", error);
    return NextResponse.json(
      { status: "error", db: String(error) },
      { status: 500 }
    );
  }
}
