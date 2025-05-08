'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
import { ResearchTab } from '@/components/ResearchTab'
import { WebSearchTab } from '@/components/WebSearchTab'
import { NewsTab } from '@/components/NewsTab'
import Link from "next/link";
import { WebpageScraperTab } from '@/components/WebpageScraperTab'
import { Sidebar, ApiConfig } from '@/components/Sidebar'

// http://ec2-13-201-189-62.ap-south-1.compute.amazonaws.com:8000

export default function Home() {
  const [apiConfig, setApiConfig] = useState<ApiConfig>({
    apiUrl: "http://localhost:8000",
    userId: "nextjs_user"
  });

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar 
        apiConfig={apiConfig}
        setApiConfig={setApiConfig}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Web Research Assistant</h1>
        
        <Tabs defaultValue="research" className="w-full">
          <TabsList className="grid grid-cols-5 mb-6">
            <TabsTrigger value="research">Research</TabsTrigger>
            <TabsTrigger value="search">Web Search</TabsTrigger>
            <TabsTrigger value="news">News</TabsTrigger>
            <TabsTrigger value="scraper">Webpage Scraper</TabsTrigger>
            <TabsTrigger value="chat" className="text-gray-400 data-[state=active]:text-black"><Link href="/chat" className="no-underline">Chat Agent</Link></TabsTrigger>
          </TabsList>

          <Card>
            <CardContent className="pt-6">
              <TabsContent value="research">
                <ResearchTab apiConfig={apiConfig} />
              </TabsContent>
              
              <TabsContent value="search">
                <WebSearchTab apiConfig={apiConfig} />
              </TabsContent>
              
              <TabsContent value="news">
                <NewsTab apiConfig={apiConfig} />
              </TabsContent>
              
              <TabsContent value="scraper">
                <WebpageScraperTab apiConfig={apiConfig} />
              </TabsContent>
            </CardContent>
          </Card>
        </Tabs>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          Web Research Assistant © 2025
        </div>
      </div>
    </div>
  )
}