import '@testing-library/jest-dom';
import {
  MessageChannel,
  MessagePort,
} from 'node:worker_threads';
import {
  ReadableStream as NodeReadableStream,
  TransformStream as NodeTransformStream,
  WritableStream as NodeWritableStream,
} from 'node:stream/web';
import { TextDecoder, TextEncoder } from 'node:util';

const installBaseWebApis = () => {
  if (!global.TextDecoder) {
    global.TextDecoder = TextDecoder as typeof global.TextDecoder;
  }
  if (!global.TextEncoder) {
    global.TextEncoder = TextEncoder as typeof global.TextEncoder;
  }
  if (!global.ReadableStream) {
    global.ReadableStream = NodeReadableStream as typeof global.ReadableStream;
  }
  if (!global.TransformStream) {
    global.TransformStream = NodeTransformStream as typeof global.TransformStream;
  }
  if (!global.WritableStream) {
    global.WritableStream = NodeWritableStream as typeof global.WritableStream;
  }
  if (!global.MessageChannel) {
    global.MessageChannel = MessageChannel as unknown as typeof global.MessageChannel;
  }
  if (!global.MessagePort) {
    global.MessagePort = MessagePort as unknown as typeof global.MessagePort;
  }
};

const installFetchPrimitives = async () => {
  installBaseWebApis();

  const undici = (await import('undici')) as unknown as {
    fetch: typeof global.fetch;
    Response: typeof global.Response;
    Headers: typeof global.Headers;
    Request: typeof global.Request;
    FormData: typeof global.FormData;
    Blob?: typeof global.Blob;
  };

  const { fetch, Response, Headers, Request, FormData, Blob } = undici;

  if (!global.fetch) {
    global.fetch = fetch as typeof global.fetch;
  }
  if (!global.Response) {
    global.Response = Response as typeof global.Response;
  }
  if (!global.Headers) {
    global.Headers = Headers as typeof global.Headers;
  }
  if (!global.Request) {
    global.Request = Request as typeof global.Request;
  }
  if (!global.FormData) {
    global.FormData = FormData as typeof global.FormData;
  }
  if (!global.Blob) {
    global.Blob = Blob as typeof global.Blob;
  }
};

beforeAll(async () => {
  await installFetchPrimitives();
});
