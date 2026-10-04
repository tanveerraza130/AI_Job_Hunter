import AuthPage from "../../features/auth/AuthPage";
import SessionRedirect from "@/components/auth/SessionRedirect";

export default function SignupPage() {
  return (
    <SessionRedirect mode="public">
      <AuthPage initialMode="signup" />
    </SessionRedirect>
  );
}
