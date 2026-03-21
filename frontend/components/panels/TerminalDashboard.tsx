import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectItem } from '@/components/ui/select';
import Input from '@/components/ui/input';

export default function TerminalDashboard() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [model, setModel] = useState('tinyllama');
  const [temperature, setTemperature] = useState('0.7');
  const [maxTokens, setMaxTokens] = useState('150');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    const res = await fetch('http://localhost:8001/api/terminal/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        model,
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens),
      }),
    });
    const data = await res.json();
    setResponse(data.response);
    setLoading(false);
  };

  return (
    <div className="p-6 space-y-4">
      <Card className="shadow-xl border-2">
        <CardContent className="space-y-4 p-4">
          <h1 className="text-2xl font-bold">🧠 Bruce Terminal Dashboard</h1>

          <Textarea
            rows={6}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Type your prompt..."
          />

          <div className="grid grid-cols-2 gap-4">
            <Select value={model} onValueChange={setModel}>
              <SelectItem value="tinyllama">TinyLlama</SelectItem>
              <SelectItem value="phi3">Phi-3-mini-4k-instruct</SelectItem>
              <SelectItem value="deepseek">DeepSeek</SelectItem>
            </Select>
            <Input
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              placeholder="Temperature (e.g., 0.7)"
              type="number"
            />
            <Input
              value={maxTokens}
              onChange={(e) => setMaxTokens(e.target.value)}
              placeholder="Max Tokens (e.g., 150)"
              type="number"
            />
          </div>

          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Thinking...' : 'Ask'}
          </Button>

          {response && (
            <div className="bg-muted p-4 rounded-xl whitespace-pre-wrap border">
              <strong className="block mb-2 text-lg">Response:</strong>
              {response}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
