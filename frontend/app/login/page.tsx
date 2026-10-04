import AuthPage from "../../features/auth/AuthPage";
import SessionRedirect from "@/components/auth/SessionRedirect";

export default function LoginPage() {
  return (
    <SessionRedirect mode="public">
      <AuthPage initialMode="signin" />
    </SessionRedirect>
  );
}
