import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function signUp({ username, password }) {
  // Use a valid .com domain for the fake email
  const fakeEmail = `${username}@user.com`;
  const { user, error } = await supabase.auth.signUp({
    email: fakeEmail,
    password,
    options: { data: { username } }
  });
  if (error) throw error;
  return user;
}

export async function signIn({ username, password }) {
  const fakeEmail = `${username}@user.com`;
  const { user, error } = await supabase.auth.signInWithPassword({
    email: fakeEmail,
    password
  });
  if (error) throw error;
  return user;
}