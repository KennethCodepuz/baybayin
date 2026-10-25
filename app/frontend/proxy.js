import { NextResponse } from 'next/server';

export function proxy(request) {
  if (request.cookies.get('baybayin-developer-access')?.value === 'local-approved') return NextResponse.next();
  return NextResponse.redirect(new URL('/developer-login', request.url));
}

export const config = { matcher: ['/developer/:path*', '/developer-reference-library/:path*', '/developer-validation/:path*'] };
