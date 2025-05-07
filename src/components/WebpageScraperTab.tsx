'use client'

import { useState } from 'react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { makeApiRequest } from '@/utils/api'
import { Loader2 } from "lucide-react"
import { ApiConfig } from './Sidebar'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface ScrapedMetadata {
  title?: string;
  url?: string;
  description?: string;
}

interface ScrapedResponse {
  status: string;
  metadata?: ScrapedMetadata;
  summarized_content?: string;
  raw_content?: string;
  message?: string;
}

interface WebpageScraperTabProps {
  apiConfig: ApiConfig;
}

export function WebpageScraperTab({ apiConfig }: WebpageScraperTabProps) {
  const [urlInput, setUrlInput] = useState('')
  const [selector, setSelector] = useState('')
  const [timeout, setTimeout] = useState(10)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scrapedData, setScrapedData] = useState<ScrapedResponse | null>(null)

  const handleScrape = async () => {
    if (!urlInput.trim()) {
      setError('Please enter a webpage URL');
      return;
    }

    // Simple URL validation
    if (!urlInput.startsWith('http://') && !urlInput.startsWith('https://')) {
      setError('Please enter a valid URL (including http:// or https://)');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await makeApiRequest('scrape', {
        url: urlInput,
        user_id: apiConfig.userId,
        selector_query: selector,
        timeout: timeout
      }, apiConfig.apiUrl) as ScrapedResponse;

      if (result && result.status === 'success') {
        setScrapedData(result);
      } else {
        setError(result?.message || 'Scraping failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Webpage Scraper & Summarizer</h2>
      
      <div className="space-y-4">
        <div>
          <Label htmlFor="url-input">Webpage URL</Label>
          <Input 
            id="url-input"
            placeholder="Enter full URL (including http:// or https://)"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
          />
        </div>
        
        <div>
          <Label htmlFor="selector-input">Selector Query (Optional)</Label>
          <Input 
            id="selector-input"
            placeholder="E.g., 'Main content about AI'"
            value={selector}
            onChange={(e) => setSelector(e.target.value)}
          />
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label>Timeout: {timeout} seconds</Label>
            <span className="text-gray-500 text-sm">{timeout} seconds</span>
          </div>
          <Slider 
            value={[timeout]} 
            min={5} 
            max={30}
            step={1}
            onValueChange={(value) => setTimeout(value[0])}
            className="py-4"
          />
        </div>
        
        <Button 
          onClick={handleScrape} 
          disabled={isLoading}
          className="w-full md:w-auto"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 
              Scraping webpage...
            </>
          ) : (
            'Scrape Webpage'
          )}
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {scrapedData && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4">Scraped Content</h3>
          
          <Card className="mb-6">
            <CardContent className="pt-6">
              <h4 className="font-semibold text-lg mb-2">Metadata</h4>
              {scrapedData.metadata && (
                <div className="space-y-2">
                  <p><strong>Title:</strong> {scrapedData.metadata.title || 'Unknown'}</p>
                  <p>
                    <strong>URL:</strong>{' '}
                    <a 
                      href={scrapedData.metadata.url || urlInput} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {scrapedData.metadata.url || urlInput}
                    </a>
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
          
          {scrapedData.summarized_content ? (
            <Card>
              <CardContent className="pt-6">
                <h4 className="font-semibold text-lg mb-2">Summary</h4>
                <div className="prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {scrapedData.summarized_content}
                  </ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Alert>
              <AlertDescription>No content could be extracted from the webpage</AlertDescription>
            </Alert>
          )}

          {scrapedData.raw_content && (
            <Card className="mt-6">
              <CardContent className="pt-6">
                <h4 className="font-semibold text-lg mb-2">Raw Content</h4>
                <div className="prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {scrapedData.raw_content}
                  </ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}