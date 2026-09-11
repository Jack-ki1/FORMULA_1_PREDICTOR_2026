import { type DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    apiToken?: string;
    apiUserId?: number;
    user?: DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    apiToken?: string;
    apiUserId?: number;
  }
}
