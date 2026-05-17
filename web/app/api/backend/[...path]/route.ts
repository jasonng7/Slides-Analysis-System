export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxy(request: Request, context: RouteContext) {
  const backendBase = process.env.BACKEND_API_BASE_URL?.replace(/\/$/, "");
  if (!backendBase) {
    return Response.json(
      { detail: "BACKEND_API_BASE_URL is not configured in Vercel." },
      { status: 500 }
    );
  }

  const { path } = await context.params;
  const requestUrl = new URL(request.url);
  const backendUrl = new URL(`${backendBase}/${path.join("/")}`);
  backendUrl.search = requestUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const response = await fetch(backendUrl, {
    method: request.method,
    headers,
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store"
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders
  });
}

export async function GET(request: Request, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return proxy(request, context);
}
