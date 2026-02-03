import { NextResponse } from "next/server";

interface SlidesRequest {
  title: string;
  outline: string[];
  language: string;
  tone: string;
  numSlides: number;
}

// FastAPI 统一网关 URL
const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

async function* generateSlidesStream(serverUrl: string, slidesRequest: SlidesRequest): AsyncGenerator<string> {
  try {
    const response = await fetch(`${serverUrl}/api/ppt/slides/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: slidesRequest.title,
        outline: slidesRequest.outline,
        language: slidesRequest.language,
        tone: slidesRequest.tone,
        numSlides: slidesRequest.numSlides,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("FastAPI error response:", errorText);
      yield JSON.stringify({ type: "error", data: `Failed to generate slides. Status: ${response.status}` }) + "\n";
      return;
    }

    // 处理 NDJSON 流式响应
    const reader = response.body?.getReader();
    if (!reader) {
      yield JSON.stringify({ type: "error", data: "No response body" }) + "\n";
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.trim()) {
          try {
            // 直接透传 NDJSON 行
            const parsed = JSON.parse(line);
            console.log("Received event:", parsed);
            yield line + "\n";
          } catch (e) {
            // 如果不是 JSON，直接透传
            console.log("Non-JSON line:", line);
            yield line + "\n";
          }
        }
      }
    }
  } catch (error) {
    console.error("Error communicating with FastAPI gateway:", error);
    yield JSON.stringify({ type: "error", data: (error as Error).message }) + "\n";
  }
}

export async function POST(req: Request) {
  try {
    const { title, outline, language, tone, numSlides } = (await req.json()) as SlidesRequest;

    if (!title || !outline || !Array.isArray(outline) || !language) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const stream = new ReadableStream({
      async start(controller) {
        const generator = generateSlidesStream(FASTAPI_URL, {
          title,
          outline,
          language,
          tone,
          numSlides,
        });

        for await (const chunk of generator) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Transfer-Encoding": "chunked",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    console.error("Error in presentation generation:", error);
    return NextResponse.json({ error: "Failed to generate presentation slides" }, { status: 500 });
  }
}
