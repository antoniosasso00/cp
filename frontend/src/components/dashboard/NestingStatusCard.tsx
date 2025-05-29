import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface NestingStatusCardProps {
  data?: any;
}

export const NestingStatusCard: React.FC<NestingStatusCardProps> = ({ data }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Stato Nesting</CardTitle>
        <CardDescription>Informazioni sui nesting in corso</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center">
          <div className="text-2xl font-bold">0</div>
          <div className="text-sm text-muted-foreground">Nesting attivi</div>
        </div>
      </CardContent>
    </Card>
  );
}; 