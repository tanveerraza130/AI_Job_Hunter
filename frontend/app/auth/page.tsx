import AuthPage from "@/features/auth/AuthPage";
import SessionRedirect from "@/components/auth/SessionRedirect";

export default function Page() {
  return (
    <SessionRedirect mode="public">
      <AuthPage />
    </SessionRedirect>
  );
}
