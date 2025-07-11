'use client'

import { useState } from 'react'
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from "@/components/ui/accordion"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { makeApiRequest } from '@/utils/api'
import { Loader2 } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Define interface for API configuration
interface ApiConfig {
  apiUrl: string;
  userId: string;
}

// Define interfaces for research data structure
interface Source {
  name?: string;
  url: string;
  snippet?: string;
  summarized_content?: string;
}

interface QueryAnalysis {
  intent?: string;
  components?: string[];
  search_strategy?: string;
  relevant_sources?: string[];
  ambiguities?: string[];
}

interface AdditionalInfo {
  web_sources?: number;
  news_sources?: number;
  contradictions?: string;
  additional_research_suggestions?: string;
}

interface ResearchData {
  query: string;
  timestamp: string;
  answer?: string;
  sources?: Source[];
  query_analysis?: QueryAnalysis;
  additional_info?: AdditionalInfo;
  research_depth?: string;
}

// Define research depth options
type ResearchDepth = 'quick' | 'standard' | 'deep';


/**
 * ResearchTab Component
 * 
 * A sophisticated React component that provides comprehensive research capabilities with
 * multiple depth levels and detailed analysis of research queries and results.
 * 
 * @component
 * @description
 * This component implements a research interface that combines web search, news analysis,
 * and content summarization to provide in-depth research results. It supports multiple
 * research depth levels and provides detailed analysis of the research query and results.
 * 
 * Features:
 * - Multi-depth research capabilities (quick, standard, deep)
 * - Query intent analysis and component breakdown
 * - Source tracking and content summarization
 * - Contradiction detection in research results
 * - Additional research suggestions
 * - Tabbed interface for organized result display
 * - Markdown support for rich text rendering
 * 
 * Data Structures:
 * 
 * @interface Source
 * @property {string} [name] - Name or title of the source
 * @property {string} url - URL of the source
 * @property {string} [snippet] - Brief excerpt from the source
 * @property {string} [summarized_content] - AI-generated summary of the source content
 * 
 * @interface QueryAnalysis
 * @property {string} [intent] - Detected intent of the research query
 * @property {string[]} [components] - Breakdown of query components
 * @property {string} [search_strategy] - Strategy used for research
 * @property {string[]} [relevant_sources] - List of relevant source types
 * @property {string[]} [ambiguities] - Identified ambiguities in the query
 * 
 * @interface AdditionalInfo
 * @property {number} [web_sources] - Number of web sources used
 * @property {number} [news_sources] - Number of news sources used
 * @property {string} [contradictions] - Identified contradictions in research
 * @property {string} [additional_research_suggestions] - Suggested follow-up research
 * 
 * @interface ResearchData
 * @property {string} query - Original research query
 * @property {string} timestamp - When research was completed
 * @property {string} [answer] - Main research findings
 * @property {Source[]} [sources] - List of information sources
 * @property {QueryAnalysis} [query_analysis] - Analysis of the query
 * @property {AdditionalInfo} [additional_info] - Supplementary information
 * @property {string} [research_depth] - Depth level used
 * 
 * Props:
 * @param {Object} apiConfig - Configuration object for API requests
 * @param {string} apiConfig.apiUrl - Base URL for API requests
 * @param {string} apiConfig.userId - User identifier for API requests
 * 
 * State:
 * @property {string} researchQuery - Current research query
 * @property {ResearchDepth} researchDepth - Selected research depth level
 * @property {boolean} isLoading - Loading state indicator
 * @property {string|null} error - Error message if any
 * @property {ResearchData|null} researchData - Research results and analysis
 * 
 * Research Depth Levels:
 * - quick: Basic research with minimal sources
 * - standard: Comprehensive research with balanced depth
 * - deep: In-depth research with extensive source analysis
 * 
 * @example
 * // Basic usage
 * <ResearchTab apiConfig={{ apiUrl: 'https://api.example.com', userId: 'user123' }} />
 * 
 * @example
 * // Example of expected research data structure
 * const researchData = {
 *   query: "Impact of AI on healthcare",
 *   timestamp: "2024-03-20T10:30:00Z",
 *   answer: "Comprehensive analysis of AI in healthcare...",
 *   sources: [
 *     {
 *       name: "Medical Journal Article",
 *       url: "https://example.com/article",
 *       snippet: "Key findings about AI in healthcare...",
 *       summarized_content: "Summary of the article..."
 *     }
 *   ],
 *   query_analysis: {
 *     intent: "Understand AI's impact on healthcare",
 *     components: ["AI", "healthcare", "impact analysis"],
 *     search_strategy: "Combined medical journals and news sources",
 *     relevant_sources: ["medical journals", "healthcare news"],
 *     ambiguities: ["Time period not specified"]
 *   },
 *   additional_info: {
 *     web_sources: 5,
 *     news_sources: 3,
 *     contradictions: "Some sources disagree on timeline",
 *     additional_research_suggestions: "Consider specific AI applications"
 *   },
 *   research_depth: "deep"
 * }
 * 
 * @returns {JSX.Element} A comprehensive research interface with detailed analysis display
 * 
 * @throws {Error} When API request fails or returns invalid data
 * 
 * @see makeApiRequest - For API request implementation
 * @see ReactMarkdown - For content rendering
 */


export function ResearchTab({ apiConfig }: { apiConfig: ApiConfig }) {
  const [researchQuery, setResearchQuery] = useState<string>('')
  const [researchDepth, setResearchDepth] = useState<ResearchDepth>('standard')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [researchData, setResearchData] = useState<ResearchData | null>(null)

  const handleResearch = async (): Promise<void> => {
    if (!researchQuery.trim()) {
      setError('Please enter a research query');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await makeApiRequest('research', {
        query: researchQuery,
        depth: researchDepth,
        user_id: apiConfig.userId
      }, apiConfig.apiUrl);

      if (result && result.status === 'success') {
        setResearchData(result.result);
      } else {
        setError(result?.message || 'Research failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Comprehensive Research</h2>
      
      <div className="space-y-4">
        <Textarea 
          placeholder="Enter your research question..." 
          className="min-h-[100px]"
          value={researchQuery}
          onChange={(e) => setResearchQuery(e.target.value)}
        />
        
        <div className="flex items-center gap-4">
          <div className="w-56">
            <Select
              value={researchDepth}
              onValueChange={(value: ResearchDepth) => setResearchDepth(value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Research Depth" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="quick">Quick</SelectItem>
                <SelectItem value="standard">Standard</SelectItem>
                <SelectItem value="deep">Deep</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Button 
            onClick={handleResearch} 
            disabled={isLoading}
            className="ml-auto"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 
                Researching...
              </>
            ) : (
              'Start Research'
            )}
          </Button>
        </div>
        
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>

      {researchData && (
        <div className="mt-8 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">
              Research Results for: {researchData.query}
            </h3>
            <p className="text-sm text-gray-500">
              Completed on: {researchData.timestamp}
            </p>
          </div>

          <Tabs defaultValue="answer" className="w-full">
            <TabsList className="grid grid-cols-4">
              <TabsTrigger value="answer">Answer</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
              <TabsTrigger value="analysis">Analysis</TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
            </TabsList>

            <TabsContent value="answer" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="prose max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {researchData.answer || ''}
                    </ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="sources" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  {researchData.sources && researchData.sources.length > 0 ? (
                    <Accordion type="single" collapsible className="w-full">
                      {researchData.sources.map((source, index) => (
                        <AccordionItem key={index} value={`source-${index}`}>
                          <AccordionTrigger>
                            {index + 1}. {source.name || 'Unnamed Source'}
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="space-y-2">
                              <p className="font-semibold">URL:</p>
                              <p>
                                <a 
                                  href={source.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline"
                                >
                                  {source.url}
                                </a>
                              </p>
                              
                              <p className="font-semibold mt-4">Snippet:</p>
                              <p>{source.snippet || 'No snippet available'}</p>
                              
                              {source.summarized_content && (
                                <>
                                  <p className="font-semibold mt-4">Summary:</p>
                                  <div className="prose max-w-none">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                      {source.summarized_content}
                                    </ReactMarkdown>
                                  </div>
                                </>
                              )}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  ) : (
                    <p>No sources provided in the research results.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="analysis" className="mt-4">
              <Card>
                <CardContent className="pt-6 space-y-6">
                  {researchData.query_analysis ? (
                    <>
                      <div>
                        <h4 className="text-lg font-semibold">Query Intent</h4>
                        <p className="mt-2">{researchData.query_analysis.intent || 'No intent analysis available.'}</p>
                      </div>
                      
                      <div>
                        <h4 className="text-lg font-semibold">Query Components</h4>
                        {researchData.query_analysis.components && researchData.query_analysis.components.length > 0 ? (
                          <ul className="mt-2 list-disc pl-5">
                            {researchData.query_analysis.components.map((comp, idx) => (
                              <li key={idx}>{comp}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-2">No component analysis available.</p>
                        )}
                      </div>

                      <div>
                        <h4 className="text-lg font-semibold">Search Strategy</h4>
                        {researchData.query_analysis.search_strategy ? (
                          <pre className="mt-2 p-4 bg-gray-100 rounded overflow-x-auto">
                            {researchData.query_analysis.search_strategy}
                          </pre>
                        ) : (
                          <p className="mt-2">No search strategy information available.</p>
                        )}
                      </div>

                      <div>
                        <h4 className="text-lg font-semibold">Relevant Sources</h4>
                        {researchData.query_analysis.relevant_sources && researchData.query_analysis.relevant_sources.length > 0 ? (
                          <ul className="mt-2 list-disc pl-5">
                            {researchData.query_analysis.relevant_sources.map((source, idx) => (
                              <li key={idx}>{source}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-2">No relevant sources information available.</p>
                        )}
                      </div>

                      <div>
                        <h4 className="text-lg font-semibold">Ambiguities</h4>
                        {researchData.query_analysis.ambiguities && researchData.query_analysis.ambiguities.length > 0 ? (
                          <ul className="mt-2 list-disc pl-5">
                            {researchData.query_analysis.ambiguities.map((ambiguity, idx) => (
                              <li key={idx}>{ambiguity}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-2">No ambiguities identified.</p>
                        )}
                      </div>
                    </>
                  ) : (
                    <p>No analysis data available.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="details" className="mt-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-center text-2xl">
                          {researchData.additional_info?.web_sources || 0}
                        </CardTitle>
                        <CardDescription className="text-center">
                          Web Sources
                        </CardDescription>
                      </CardHeader>
                    </Card>
                    
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-center text-2xl">
                          {researchData.additional_info?.news_sources || 0}
                        </CardTitle>
                        <CardDescription className="text-center">
                          News Sources
                        </CardDescription>
                      </CardHeader>
                    </Card>
                    
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-center text-2xl">
                          {researchData.research_depth || 'standard'}
                        </CardTitle>
                        <CardDescription className="text-center">
                          Research Depth
                        </CardDescription>
                      </CardHeader>
                    </Card>
                  </div>

                  {researchData.additional_info?.contradictions && (
                    <div className="mt-6">
                      <h4 className="text-lg font-semibold">Contradictions Found</h4>
                      <p className="mt-2">{researchData.additional_info.contradictions}</p>
                    </div>
                  )}

                  {researchData.additional_info?.additional_research_suggestions && (
                    <div className="mt-6">
                      <h4 className="text-lg font-semibold">Additional Research Suggestions</h4>
                      <p className="mt-2">{researchData.additional_info.additional_research_suggestions}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}