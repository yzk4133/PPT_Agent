import { NextResponse } from "next/server";
import { LangChainAdapter } from "ai";
import crypto from "node:crypto";

interface OutlineRequest {
  prompt: string;
  numberOfCards: number;
  language: string;
}

function generateId() {
  return crypto.randomUUID();
}

// FastAPI 统一网关 URL
const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

console.log("FastAPI Gateway URL:", FASTAPI_URL);

/**
 * Creates an async generator that streams text content from the FastAPI gateway.
 * @param serverUrl - The URL of the FastAPI gateway.
 * @param content - The user input (e.g., title for outline generation).
 * @yields Each chunk of text received from the gateway.
 */

function iteratorToStream(iterator: AsyncGenerator<string>): ReadableStream<string> {
  return new ReadableStream({
    async pull(controller) {
      const { value, done } = await iterator.next();
      if (done) {
        controller.close();
      } else {
        controller.enqueue(value);
      }
    },
  });
}

async function* generateOutlineStream(serverUrl: string, content: string, language: string) {
  try {
    const response = await fetch(`${serverUrl}/api/ppt/outline/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: content,
        numberOfCards: 10,
        language: language,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("FastAPI error response:", errorText);
      yield `Error: Failed to generate outline. Status: ${response.status}`;
      return;
    }

    // 处理 SSE 流式响应
    const reader = response.body?.getReader();
    if (!reader) {
      yield "Error: No response body";
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
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              console.log("Yielding content chunk:", data.content);
              yield data.content;
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
      }
    }
  } catch (error) {
    console.error("Error communicating with FastAPI gateway:", error);
    yield `Error: Failed to communicate with gateway. ${error}`;
  }
}

export async function POST(request: Request) {
  try {
    const { prompt, numberOfCards, language } = (await request.json()) as OutlineRequest;

    if (!prompt || !numberOfCards || !language) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const stream = iteratorToStream(generateOutlineStream(FASTAPI_URL, prompt, language));
    return LangChainAdapter.toDataStreamResponse(stream);
  } catch (error) {
    console.error("Error in presentation outline:", error);
    return NextResponse.json(
      { error: "Failed to generate presentation outline" },
      { status: 500 }
    );
  }
}
