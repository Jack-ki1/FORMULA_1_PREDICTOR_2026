import NextAuth from "next-auth";
import type { Provider } from "next-auth/providers";
import GitHub from "next-auth/providers/github";
import Credentials from "next-auth/providers/credentials";

const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function syncUser(profile: {
  provider: string;
  provider_account_id: string;
  email?: string | null;
  display_name: string;
  avatar_url?: string | null;
}): Promise<{ token: string; user_id: number } | null> {
  try {
    const res = await fetch(`${API_INTERNAL_URL}/auth/sync-user`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-sync-secret": process.env.AUTH_SYNC_SECRET ?? "" },
      body: JSON.stringify(profile),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

const providers: Provider[] = [
  GitHub({
    clientId: process.env.AUTH_GITHUB_ID,
    clientSecret: process.env.AUTH_GITHUB_SECRET,
  }),
];

// Dev-mode-only: lets anyone run/test the app locally (or a preview
// deploy) without setting up a real GitHub OAuth app first. Never
// registered outside development — see the NODE_ENV guard below.
if (process.env.NODE_ENV !== "production") {
  providers.push(
    Credentials({
      id: "dev-login",
      name: "Dev login (no OAuth needed)",
      credentials: { name: { label: "Display name", type: "text" } },
      async authorize(credentials) {
        const name = (credentials?.name as string) || "Dev User";
        return { id: `dev:${name}`, name, email: `${name.toLowerCase().replace(/\s+/g, "-")}@dev.local` };
      },
    })
  );
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers,
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user, account }) {
      // Only re-sync on actual sign-in (account is only present then),
      // not on every subsequent session read.
      if (user && account) {
        const provider = account.provider === "dev-login" ? "dev" : account.provider;
        const providerAccountId = account.providerAccountId ?? user.id ?? "unknown";
        const synced = await syncUser({
          provider,
          provider_account_id: providerAccountId,
          email: user.email,
          display_name: user.name ?? "F1 Fan",
          avatar_url: user.image,
        });
        if (synced) {
          token.apiToken = synced.token;
          token.apiUserId = synced.user_id;
        }
      }
      return token;
    },
    async session({ session, token }) {
      session.apiToken = token.apiToken as string | undefined;
      session.apiUserId = token.apiUserId as number | undefined;
      return session;
    },
  },
  pages: {
    signIn: "/account",
  },
});
