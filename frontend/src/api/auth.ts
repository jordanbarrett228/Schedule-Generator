// src/api/auth.ts
export async function login(username: string, password: string) {
  const res = await fetch("/api/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      username,
      password,
    }),
  });

  if (!res.ok) {
    throw new Error("Invalid username or password");
  }

  return res.json(); // { access_token, token_type }
}
