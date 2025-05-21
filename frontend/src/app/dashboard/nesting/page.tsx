'use client';

import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import AutoNestingTab from './auto-tab';
import ManualNestingTab from './manual-tab';
import ResultsTab from './results-tab';

export default function NestingPage() {
    const [activeTab, setActiveTab] = useState('auto');
    
    return (
        <div className="container mx-auto py-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Nesting Autoclavi</h1>
            </div>
            
            <Tabs
                defaultValue="auto"
                value={activeTab}
                onValueChange={setActiveTab}
                className="w-full"
            >
                <TabsList className="grid w-full grid-cols-3 mb-6">
                    <TabsTrigger value="auto">Automatico</TabsTrigger>
                    <TabsTrigger value="manual">Manuale</TabsTrigger>
                    <TabsTrigger value="results">Risultati</TabsTrigger>
                </TabsList>
                
                <TabsContent value="auto">
                    <AutoNestingTab />
                </TabsContent>
                
                <TabsContent value="manual">
                    <ManualNestingTab />
                </TabsContent>
                
                <TabsContent value="results">
                    <ResultsTab />
                </TabsContent>
            </Tabs>
        </div>
    );
} 