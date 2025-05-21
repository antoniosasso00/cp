import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Plus, Trash2 } from 'lucide-react';

interface Parte {
  id: number;
  part_number: string;
  descrizione_breve: string;
  tools: Array<{
    id: number;
    codice: string;
    descrizione: string;
  }>;
}

interface SelectedParte {
  parte_id: number;
  quantity: number;
}

export function ODLForm() {
  const [parti, setParti] = useState<Parte[]>([]);
  const [selectedParti, setSelectedParti] = useState<SelectedParte[]>([]);
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchParti();
  }, []);

  const fetchParti = async () => {
    try {
      const response = await fetch('/api/parti');
      const data = await response.json();
      setParti(data);
    } catch (error) {
      console.error('Errore nel caricamento delle parti:', error);
      setError('Errore nel caricamento delle parti');
    }
  };

  const handleAddParte = () => {
    setSelectedParti([...selectedParti, { parte_id: 0, quantity: 1 }]);
  };

  const handleRemoveParte = (index: number) => {
    setSelectedParti(selectedParti.filter((_, i) => i !== index));
  };

  const handleParteChange = (index: number, field: keyof SelectedParte, value: number) => {
    const newParti = [...selectedParti];
    newParti[index] = { ...newParti[index], [field]: value };
    setSelectedParti(newParti);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/odl', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          description,
          parti: selectedParti,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Errore nella creazione dell\'ODL');
      }

      router.push('/odl');
    } catch (error) {
      console.error('Errore nella creazione dell\'ODL:', error);
      setError(error instanceof Error ? error.message : 'Errore nella creazione dell\'ODL');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Nuovo Ordine di Lavorazione</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="code">Codice ODL</Label>
            <Input
              id="code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Descrizione</Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label>Parti</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddParte}
              >
                <Plus className="w-4 h-4 mr-2" />
                Aggiungi Parte
              </Button>
            </div>

            {selectedParti.map((selectedParte, index) => (
              <Card key={index} className="p-4">
                <div className="flex justify-between items-start space-x-4">
                  <div className="flex-1 space-y-4">
                    <div className="space-y-2">
                      <Label>Parte</Label>
                      <Select
                        value={selectedParte.parte_id.toString()}
                        onValueChange={(value) => handleParteChange(index, 'parte_id', parseInt(value))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Seleziona una parte" />
                        </SelectTrigger>
                        <SelectContent>
                          {parti.map((parte) => (
                            <SelectItem key={parte.id} value={parte.id.toString()}>
                              {parte.part_number} - {parte.descrizione_breve}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Quantità</Label>
                      <Input
                        type="number"
                        min="1"
                        value={selectedParte.quantity}
                        onChange={(e) => handleParteChange(index, 'quantity', parseInt(e.target.value))}
                      />
                    </div>

                    {selectedParte.parte_id > 0 && (
                      <div className="text-sm text-gray-500">
                        <p>Tools: {parti.find(p => p.id === selectedParte.parte_id)?.tools.map(t => t.codice).join(', ')}</p>
                      </div>
                    )}
                  </div>

                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveParte(index)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex justify-end space-x-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Annulla
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creazione...' : 'Crea ODL'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  );
} 