'use client'

import { useState } from 'react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent } from "@/components/ui/card"
import { makeApiRequest } from '@/utils/api'
import { Loader2 } from "lucide-react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Define interface for API configuration
interface ApiConfig {
  apiUrl: string;
  userId: string;
}

// Define interfaces for search results
interface SearchContext {
  name?: string;
  url: string;
  snippet?: string;
  content?: string;
  summary?: string;
}

interface SearchImage {
  imageUrl: string;
  title?: string;
  link?: string;
}

interface SearchStory {
  title?: string;
  imageUrl?: string;
  source?: string;
  date?: string;
  link: string;
}

interface RelatedSearch {
  query: string;
}

interface SearchResults {
  contexts?: SearchContext[];
  images?: SearchImage[];
  stories?: SearchStory[];
  relatedSearches?: RelatedSearch[];
}

export function WebSearchTab({ apiConfig }: { apiConfig: ApiConfig }) {
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null)

  const handleSearch = async (): Promise<void> => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await makeApiRequest('search', {
        query: searchQuery,
        user_id: apiConfig.userId
      }, apiConfig.apiUrl);

      if (result) {
        setSearchResults(result);
      } else {
        setError('Search failed or returned no results');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Quick Web Search</h2>
      
      <div className="flex space-x-4">
        <Input 
          placeholder="Enter search terms..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
        />
        
        <Button 
          onClick={handleSearch} 
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 
              Searching...
            </>
          ) : (
            'Search'
          )}
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {searchResults && (
        <div className="mt-8 space-y-8">
          {/* Display contexts (main search results) */}
          {searchResults.contexts && searchResults.contexts.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-4">Search Results</h3>
              <Accordion type="single" collapsible className="w-full">
                {searchResults.contexts.map((context, index) => (
                  <AccordionItem key={index} value={`context-${index}`}>
                    <AccordionTrigger>
                      {index + 1}. {context.name || 'Result'}
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-2">
                        <p className="font-semibold">URL:</p>
                        <p>
                          <a 
                            href={context.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {context.url}
                          </a>
                        </p>
                        
                        <p className="font-semibold mt-4">Snippet:</p>
                        <div className="prose max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {context.snippet || 'No snippet available'}
                          </ReactMarkdown>
                        </div>

                        {context.summary && (
                          <>
                            <p className="font-semibold mt-4">Summary:</p>
                            <div className="prose max-w-none">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {context.summary}
                              </ReactMarkdown>
                            </div>
                          </>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          )}

          {/* Display news stories */}
          {searchResults.stories && searchResults.stories.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-4">News & Stories</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {searchResults.stories.map((story, index) => (
                  <Card key={index}>
                    <CardContent className="pt-6">
                      <h4 className="text-lg font-semibold mb-2">{story.title || 'Untitled'}</h4>
                      {story.imageUrl && (
                        <div className="relative w-full h-40 mb-4">
                          <img 
                            src={story.imageUrl} 
                            alt={story.title || 'News image'} 
                            className="w-full h-full object-cover rounded-md"
                          />
                        </div>
                      )}
                      <div className="flex justify-between mb-2">
                        <p className="text-sm text-gray-600">Source: {story.source || 'Unknown'}</p>
                        <p className="text-sm text-gray-600">Published: {story.date || 'No date'}</p>
                      </div>
                      <a 
                        href={story.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm"
                      >
                        Read more
                      </a>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Display related searches */}
          {searchResults.relatedSearches && searchResults.relatedSearches.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-4">Related Searches</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {searchResults.relatedSearches.map((related, index) => (
                  <div key={index} className="bg-gray-50 rounded-md p-3">
                    <p>{related.query}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Display images */}
          {searchResults.images && searchResults.images.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-4">Images</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {searchResults.images.map((image, index) => (
                  <div key={index} className="flex flex-col items-center">
                    <div className="relative w-full h-32 mb-2">
                      <img 
                        src={image.imageUrl} 
                        alt={image.title || 'Search image'} 
                        className="w-full h-full object-cover rounded-md"
                      />
                    </div>
                    <a 
                      href={image.link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm"
                    >
                      View source
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}