'use client'

import { useState } from 'react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion"
import { makeApiRequest } from '@/utils/api'
import { Loader2 } from "lucide-react"
import { ApiConfig } from './Sidebar'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface NewsArticle {
  title?: string;
  thumbnail?: string;
  source?: string;
  date?: string;
  authors?: string[];
  link?: string;
  content?: string;
  summary?: string;
}

interface NewsResponse {
  status: string;
  articles: NewsArticle[];
  metadata?: {
    query?: string;
    total_results_available?: number;
    total_results_returned?: number;
  };
  message?: string;
}

interface NewsTabProps {
  apiConfig: ApiConfig;
}

/**
 * NewsTab Component
 * 
 * A React component that provides a news search interface with filtering capabilities.
 * 
 * Features:
 * - Search news articles based on user query
 * - Filter results by time range (1-30 days)
 * - Control maximum number of results (5-50 articles)
 * - View results in either card or list format
 * - Display article details including title, source, date, authors, and summary
 * 
 * Props:
 * @param {Object} apiConfig - Configuration object for API requests
 * @param {string} apiConfig.apiUrl - Base URL for API requests
 * @param {string} apiConfig.userId - User identifier for API requests
 * 
 * State:
 * - newsQuery: string - Current search query
 * - daysBack: number - Number of days to look back (1-30)
 * - maxResults: number - Maximum number of results to show (5-50)
 * - isLoading: boolean - Loading state indicator
 * - error: string | null - Error message if any
 * - newsResults: NewsResponse | null - Search results
 * - viewMode: string - Display mode ('cards' or 'list')
 * 
 * @example
 * <NewsTab apiConfig={{ apiUrl: 'https://api.example.com', userId: 'user123' }} />
 * 
 * @returns {JSX.Element} A news search interface with results display
 */


export function NewsTab({ apiConfig }: NewsTabProps) {
  const [newsQuery, setNewsQuery] = useState('')
  const [daysBack, setDaysBack] = useState(7)
  const [maxResults, setMaxResults] = useState(20)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newsResults, setNewsResults] = useState<NewsResponse | null>(null)
  const [viewMode, setViewMode] = useState('cards')

  const handleNewsSearch = async () => {
    if (!newsQuery.trim()) {
      setError('Please enter a news topic');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await makeApiRequest('news', {
        query: newsQuery,
        days_back: daysBack,
        max_results: maxResults,
        user_id: apiConfig.userId
      }, apiConfig.apiUrl) as NewsResponse;

      if (result && result.status === 'success' && result.articles) {
        setNewsResults(result);
      } else {
        setError(result?.message || 'News search failed or returned no results');
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
      <h2 className="text-2xl font-bold">News Search</h2>
      
      <div className="space-y-4">
        <Input 
          placeholder="Enter news topic..."
          value={newsQuery}
          onChange={(e) => setNewsQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleNewsSearch();
            }
          }}
        />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Days Back: {daysBack}</Label>
              <span className="text-gray-500 text-sm">{daysBack} days</span>
            </div>
            <Slider 
              value={[daysBack]} 
              min={1} 
              max={30} 
              step={1}
              onValueChange={(value) => setDaysBack(value[0])}
              className="py-4"
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Maximum Results: {maxResults}</Label>
              <span className="text-gray-500 text-sm">{maxResults} articles</span>
            </div>
            <Slider 
              value={[maxResults]} 
              min={5} 
              max={50} 
              step={5}
              onValueChange={(value) => setMaxResults(value[0])}
              className="py-4"
            />
          </div>
        </div>
        
        <Button 
          onClick={handleNewsSearch} 
          disabled={isLoading}
          className="w-full md:w-auto"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 
              Fetching news...
            </>
          ) : (
            'Search News'
          )}
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {newsResults && newsResults.articles && (
        <div className="mt-8 space-y-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
            <h3 className="text-xl font-semibold">
              News Results for: &apos;{newsResults.metadata?.query || newsQuery}&apos;
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="flex flex-row items-center justify-between py-4">
                <p className="font-medium">Total Results</p>
                <p className="text-2xl font-bold">
                  {newsResults.metadata?.total_results_available || 'N/A'}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="flex flex-row items-center justify-between py-4">
                <p className="font-medium">Results Shown</p>
                <p className="text-2xl font-bold">
                  {newsResults.metadata?.total_results_returned || newsResults.articles.length}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="flex flex-row items-center justify-between py-4">
                <p className="font-medium">Time Range</p>
                <p className="text-2xl font-bold">Past {daysBack} days</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-end">
            <Tabs value={viewMode} onValueChange={setViewMode} className="w-auto">
              <TabsList>
                <TabsTrigger value="cards">Cards</TabsTrigger>
                <TabsTrigger value="list">List</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <div>
            {viewMode === 'cards' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {newsResults.articles.map((article, index) => (
                  <Card key={index}>
                    <CardContent className="p-6">
                      <h3 className="text-lg font-semibold mb-3">{article.title || 'Untitled'}</h3>
                      
                      {article.thumbnail && (
                        <div className="relative w-full h-48 mb-4">
                          <img 
                            src={article.thumbnail} 
                            alt={article.title || 'News thumbnail'} 
                            className="w-full h-full object-cover rounded-md"
                          />
                        </div>
                      )}
                      
                      <div className="flex flex-wrap gap-2 mb-3">
                        {article.source && (
                          <span className="text-sm text-gray-600">
                            <strong>Source:</strong> {article.source}
                          </span>
                        )}
                        
                        {article.date && (
                          <span className="text-sm text-gray-600">
                            <strong>Date:</strong> {article.date.split(',')[0]}
                          </span>
                        )}
                      </div>
                      
                      {article.authors && article.authors.length > 0 && (
                        <div className="mb-3">
                          <span className="text-sm text-gray-600">
                            <strong>By:</strong> {article.authors.join(', ')}
                          </span>
                        </div>
                      )}

                      {article.summary && (
                        <div className="prose max-w-none mb-4">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {article.summary}
                          </ReactMarkdown>
                        </div>
                      )}
                      
                      {article.link && (
                        <a 
                          href={article.link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          Read More
                        </a>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                <Accordion type="single" collapsible className="w-full">
                  {newsResults.articles.map((article, index) => (
                    article.title && (
                      <AccordionItem key={index} value={`article-${index}`}>
                        <AccordionTrigger>
                          {index + 1}. {article.title}
                        </AccordionTrigger>
                        <AccordionContent>
                          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                            {article.thumbnail && (
                              <div className="col-span-2">
                                <img 
                                  src={article.thumbnail} 
                                  alt={article.title || 'News thumbnail'} 
                                  className="w-full h-auto rounded-md"
                                />
                              </div>
                            )}
                            
                            <div className={article.thumbnail ? "col-span-3" : "col-span-5"}>
                              {article.source && (
                                <p className="mb-2"><strong>Source:</strong> {article.source}</p>
                              )}
                              
                              {article.date && (
                                <p className="mb-2"><strong>Date:</strong> {article.date}</p>
                              )}
                              
                              {article.authors && article.authors.length > 0 && (
                                <p className="mb-2"><strong>By:</strong> {article.authors.join(', ')}</p>
                              )}
                              
                              {article.link && (
                                <p className="mb-2">
                                  <strong>URL:</strong>{' '}
                                  <a 
                                    href={article.link} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                  >
                                    {article.link}
                                  </a>
                                </p>
                              )}
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    )
                  ))}
                </Accordion>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}