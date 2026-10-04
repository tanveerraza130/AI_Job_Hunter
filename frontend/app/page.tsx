import HomePage from "@/features/home/HomePage";
import SessionRedirect from "@/components/auth/SessionRedirect";

export default function Page() {
  return (
    <SessionRedirect mode="public">
      <HomePage />
    </SessionRedirect>
  );
}
