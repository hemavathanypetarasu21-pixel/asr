"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import BrandMark from "@/components/BrandMark";
import { routes, safeRedirectPath } from "@/lib/routes";
import { createClient } from "@/lib/supabase/client";

const MIN_PASSWORD_LENGTH = 8;

const authSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
  confirmPassword: z.string(),
});

const signupSchema = authSchema.superRefine((values, context) => {
  if (values.password.length < MIN_PASSWORD_LENGTH) {
    context.addIssue({ code: "custom", path: ["password"], message: `Use at least ${MIN_PASSWORD_LENGTH} characters.` });
  }
  if (values.password !== values.confirmPassword) {
    context.addIssue({ code: "custom", path: ["confirmPassword"], message: "Passwords do not match." });
  }
});

type AuthValues = z.infer<typeof authSchema>;
type AuthMode = "login" | "signup";

export default function AuthForm({ mode, next }: { mode: AuthMode; next?: string }) {
  const router = useRouter();
  const isSignup = mode === "signup";
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AuthValues>({
    resolver: zodResolver(isSignup ? signupSchema : authSchema),
    defaultValues: { email: "", password: "", confirmPassword: "" },
  });

  async function onSubmit({ email, password }: AuthValues) {
    setFormError(null);
    setNotice(null);
    const supabase = createClient();

    if (isSignup) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { emailRedirectTo: `${window.location.origin}${routes.login}` },
      });
      if (error) return setFormError(error.message);
      // No session means email confirmation is enabled in Supabase.
      if (!data.session) return setNotice("Check your inbox to confirm your email, then log in.");
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) return setFormError(error.message);
    }

    router.replace(safeRedirectPath(next));
    router.refresh();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-4 py-10">
      <section className="card w-full max-w-sm p-6 shadow-sm">
        <BrandMark href={routes.home} />
        <h1 className="mt-5 text-lg font-semibold text-heading">
          {isSignup ? "Create your account" : "Log in"}
        </h1>
        <p className="mt-1 text-[13px] text-muted">
          {isSignup
            ? "Record Manglish and Tanglish speech and translate it to English."
            : "Welcome back. Continue to your workspace."}
        </p>

        <form className="mt-5 grid gap-3" onSubmit={handleSubmit(onSubmit)} noValidate>
          <label className="field-label">
            Email
            <input className="input" type="email" autoComplete="email" aria-invalid={Boolean(errors.email)} {...register("email")} />
            {errors.email && <span className="field-error">{errors.email.message}</span>}
          </label>
          <label className="field-label">
            Password
            <input
              className="input"
              type="password"
              autoComplete={isSignup ? "new-password" : "current-password"}
              aria-invalid={Boolean(errors.password)}
              {...register("password")}
            />
            {errors.password && <span className="field-error">{errors.password.message}</span>}
          </label>
          {isSignup && (
            <label className="field-label">
              Confirm password
              <input
                className="input"
                type="password"
                autoComplete="new-password"
                aria-invalid={Boolean(errors.confirmPassword)}
                {...register("confirmPassword")}
              />
              {errors.confirmPassword && <span className="field-error">{errors.confirmPassword.message}</span>}
            </label>
          )}

          {formError && <p className="rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">{formError}</p>}
          {notice && <p className="rounded-md bg-accent-soft p-2.5 text-xs text-accent" role="status">{notice}</p>}

          <button type="submit" className="btn-primary mt-1 w-full" disabled={isSubmitting}>
            {isSubmitting ? "Please wait…" : isSignup ? "Create account" : "Log in"}
          </button>
        </form>

        <p className="mt-5 text-[13px] text-muted">
          {isSignup ? "Already have an account? " : "New here? "}
          <Link className="font-semibold text-brand hover:underline" href={isSignup ? routes.login : routes.signup}>
            {isSignup ? "Log in" : "Create an account"}
          </Link>
        </p>
      </section>
    </main>
  );
}
