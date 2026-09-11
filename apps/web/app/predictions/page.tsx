import { redirect } from "next/navigation";
import { api } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function PredictionsIndex() {
  const races = await api.races();
  const target = races.find((r) => r.status === "upcoming") ?? races[races.length - 1];
  redirect(`/predictions/${target.id}`);
}
