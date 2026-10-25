import { NextResponse } from 'next/server';

export async function POST(request) {
  const { password } = await request.json().catch(() => ({}));
  if (password !== (process.env.BAYBAYIN_DEVELOPER_PASSWORD || 'ganbatte')) {
    return NextResponse.json({ detail: 'Incorrect developer password.' }, { status: 401 });
  }
  const response = NextResponse.json({ ok: true });
  response.cookies.set('baybayin-developer-access', 'local-approved', { httpOnly: true, sameSite: 'lax', path: '/', maxAge: 60 * 60 * 8 });
  return response;
}
