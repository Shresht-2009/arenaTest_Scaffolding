/**
 * RIOS API Client
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || 'ws://localhost:8000';

export class RiosAPI {
  private baseUrl: string;
  private wsBaseUrl: string;

  constructor(baseUrl: string = API_BASE, wsBaseUrl: string = WS_BASE) {
    this.baseUrl = baseUrl;
    this.wsBaseUrl = wsBaseUrl;
  }

  async fetchDashboard(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/engine/dashboard`);
    if (!res.ok) throw new Error(`Dashboard fetch failed: ${res.status}`);
    return res.json();
  }

  async getState(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/evolution/state`);
    if (!res.ok) throw new Error(`State fetch failed`);
    return res.json();
  }

  async startEvolution(problem: string, resume: boolean = false): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/evolution/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problem, resume }),
    });
    if (!res.ok) throw new Error(`Start failed: ${await res.text()}`);
    return res.json();
  }

  async stopEvolution(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/evolution/stop`, { method: 'POST' });
    if (!res.ok) throw new Error(`Stop failed`);
    return res.json();
  }

  async getMemory(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/memory`);
    return res.json();
  }

  async getCheckpoints(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/checkpoints`);
    return res.json();
  }

  async getBenchmarkFamilies(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/benchmark/families`);
    return res.json();
  }

  async generateBenchmark(family?: string, difficulty: number = 0.5, count: number = 1): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/benchmark/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ family, difficulty, count }),
    });
    return res.json();
  }

  // WebSocket connection for real-time evolution
  connectEvolutionWebSocket(
    onMessage: (data: any) => void,
    onOpen?: () => void,
    onClose?: () => void,
    onError?: (e: Event) => void
  ): WebSocket {
    const ws = new WebSocket(`${this.wsBaseUrl}/ws/evolution`);

    ws.onopen = () => {
      console.log('WS connected');
      onOpen?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('WS parse error', e);
      }
    };

    ws.onclose = () => {
      console.log('WS closed');
      onClose?.();
    };

    ws.onerror = (e) => {
      console.error('WS error', e);
      onError?.(e);
    };

    return ws;
  }

  sendWS(ws: WebSocket, type: string, payload: any = {}) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, ...payload }));
    }
  }
}

export const api = new RiosAPI();
