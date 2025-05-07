# Web Research Agent Design Document

## 1. Overview

The Web Research Agent is an AI-powered system designed to perform comprehensive web research on behalf of users. It can search the web, extract relevant information from websites, analyze content, and synthesize findings into coherent, useful responses.

## 2. Agent Architecture

### 2.1 System Architecture Diagram

```mermaid
graph TB
    subgraph Frontend
        Streamlit[Streamlit Frontend]
    end

    subgraph Backend
        FastAPI[FastAPI Application]
        subgraph API Endpoints
            Research[/research]
            Search[/search]
            Scrape[/scrape]
            News[/news]
        end

        subgraph Core Services
            ResearchService[Research Service]
            WebScraper[Web Scraper]
            NewsAggregator[News Aggregator]
            ContentAnalyzer[Content Analyzer]
        end

        subgraph Data Layer
            Redis[(Redis Cache)]
            LLM[OpenAI GPT]
        end

        subgraph External APIs
            SerpAPI[SerpAPI]
            WebSearch[Web Search]
        end
    end

    %% Frontend to Backend connections
    Streamlit --> FastAPI

    %% API Endpoints to Core Services
    Research --> ResearchService
    Search --> WebScraper
    Scrape --> WebScraper
    News --> NewsAggregator

    %% Core Services to Data Layer
    ResearchService --> Redis
    ResearchService --> LLM
    WebScraper --> Redis
    NewsAggregator --> Redis
    ContentAnalyzer --> LLM

    %% Core Services to External APIs
    WebScraper --> WebSearch
    NewsAggregator --> SerpAPI

    %% Data Flow
    classDef frontend fill:#f9f,stroke:#333,stroke-width:2px
    classDef backend fill:#bbf,stroke:#333,stroke-width:2px
    classDef data fill:#bfb,stroke:#333,stroke-width:2px
    classDef external fill:#fbb,stroke:#333,stroke-width:2px

    class Streamlit frontend
    class FastAPI,API,Core backend
    class Redis,LLM data
    class SerpAPI,WebSearch external
```


### 2.2 Decision Flow Process

1. **Query Analysis**: The agent first analyzes the user query to determine:
   - Research intent (factual information, opinion, news, etc.)
   - Key components of the query
   - Appropriate search strategy
   - Required information types

2. **Search Strategy Selection**: Based on query analysis, the agent selects the optimal search approach:
   - General web search for factual queries
   - News aggregation for current events
   - Deep scraping for comprehensive research needs

3. **Information Gathering**: The agent executes the search strategy and collects information from multiple sources.

4. **Content Processing**: Raw content is processed to:
   - Extract relevant information
   - Analyze reliability and relevance
   - Identify contradictions or gaps
   - Summarize key points

5. **Information Synthesis**: The agent combines information from all sources to:
   - Resolve contradictions
   - Organize information logically
   - Generate a comprehensive answer
   - Cite sources appropriately

6. **Response Generation**: A final response is prepared that directly addresses the user's query.

### 2.3 Error Handling

The agent employs robust error handling at each stage:

- **Unreachable Websites**: If a website is unreachable, the agent logs the error, continues with available sources, and notes the limitation in the final response.
- **Rate Limiting**: Implements exponential backoff and rotates user agents to handle rate limiting.
- **Parsing Failures**: If content extraction fails, the agent falls back to snippets provided by search APIs.
- **Contradictory Information**: The agent identifies contradictions, evaluates source reliability, and presents the most credible information with appropriate caveats.
- **Timeout Handling**: All web operations have configurable timeouts with appropriate fallback mechanisms.

## 3. Tool Integration

### 3.1 Web Search Tool

**Input**: User query, search parameters (depth, result limit)  
**Output**: Search results with URLs, titles, and snippets  
**Implementation**: Uses the Serper API to perform Google searches with configurable parameters.  
**Decision Making**: Results are ranked by relevance and selected for further processing based on query relevance.

### 3.2 Web Scraper/Crawler

**Input**: URL, optional selectors for targeted extraction  
**Output**: Structured content including main text, headings, tables, and links  
**Implementation**: 
- Basic scraper uses BeautifulSoup for HTML parsing
- Advanced scraper uses Pyppeteer (Puppeteer Python port) for JavaScript-rendered content
- Content is converted to markdown for consistent processing

**Decision Making**: Determines content relevance and extracts key information based on structural elements and semantic context.

### 3.3 Content Analyzer

**Input**: Extracted content, analysis criteria  
**Output**: Content analysis with scores and explanations for relevance, reliability, bias, factuality, and recency  
**Implementation**: Uses LLM (GPT-4o-mini) to evaluate content based on predefined criteria.  
**Decision Making**: Analysis results inform source prioritization and synthesis, with higher-scoring content given more weight.

### 3.4 News Aggregator

**Input**: News-related query, time range, result limit  
**Output**: Recent news articles with source, date, title, and snippet  
**Implementation**: Uses specialized search queries and filters to focus on news sources.  
**Decision Making**: News is prioritized by recency and relevance, with particular attention to source credibility.

## 4. Core Agent Capabilities

### 4.1 Query Analysis

The agent analyzes queries to:
- Identify research intent (factual, exploratory, news, etc.)
- Break down complex questions into components
- Detect time sensitivity (recent vs. historical information)
- Determine appropriate source types (academic, news, encyclopedic, etc.)

Implementation: Uses LLM with specialized prompting to extract query characteristics and formulate research strategy.

### 4.2 Web Search

The agent formulates effective search strategies by:
- Generating appropriate search terms from the query
- Applying domain-specific modifiers when relevant
- Adapting search terms based on initial results
- Filtering results by relevance and credibility

Implementation: Combines API-based search with intelligent query refinement.

### 4.3 Content Extraction

The agent extracts information from websites by:
- Identifying and parsing key structural elements (headings, paragraphs, tables)
- Distinguishing between primary content and navigation/ads
- Handling different content types appropriately
- Respecting robots.txt and implementing rate limiting

Implementation: Uses multiple extraction techniques (BeautifulSoup for basic HTML, Pyppeteer for JavaScript-rendered content).

### 4.4 Information Synthesis

The agent synthesizes information by:
- Combining data from multiple sources
- Resolving contradictions based on source reliability
- Organizing information in a logical structure
- Generating concise summaries that address the original query
- Citing sources appropriately

Implementation: Uses advanced LLM capabilities to process and synthesize multiple sources.

## 5. Technical Implementation

### 5.1 Core Technologies

- **Python**: Primary programming language
- **OpenAI GPT-4o/GPT-4o-mini**: For natural language understanding and generation
- **BeautifulSoup**: For HTML parsing
- **Pyppeteer**: For JavaScript-rendered content
- **Asyncio**: For efficient concurrent operations
- **Redis**: For caching search results and extracted content

### 5.2 Key Features

- **Asynchronous Processing**: All web operations are asynchronous for improved performance
- **Caching System**: Results are cached to reduce redundant operations and API calls
- **Modular Design**: Components can be used independently or as part of the full pipeline
- **Configurable Research Depth**: Users can specify quick, standard, or deep research modes
- **Error Resilience**: Robust error handling and fallback mechanisms
- **Source Attribution**: All information is properly attributed to its source

### 5.3 Security and Ethical Considerations

- **Rate Limiting**: Implements respectful crawling practices
- **User Agent Rotation**: Prevents IP blocking
- **Robots.txt Compliance**: Respects website crawling policies
- **Content Attribution**: Properly attributes information to sources
- **Privacy Consciousness**: Does not store unnecessary user data

## 6. Testing Strategy

- **Unit Tests**: Individual components tested in isolation
- **Integration Tests**: Tests for interactions between components
- **End-to-End Tests**: Complete research flows with various query types
- **Error Case Testing**: Tests for handling of various error conditions
- **Performance Testing**: Metrics for response time and resource usage

## 7. Future Improvements

- Enhanced multi-language support
- Integration with academic search APIs
- Image and video content analysis
- Improved fact-checking capabilities
- User feedback incorporation for continuous improvement
- Expandable plugin system for additional data sources

User Query → FastAPI → Web Scraper → 
Content Extraction → Content Analysis → 
Redis Cache → Response


# System Architecture: Web Research and Analysis System

## Overview
This system is designed to process user queries, perform web research, analyze content, and provide synthesized information. The architecture follows a modular design with clear separation of concerns.

## System Components

### 1. Query Processing Layer
```mermaid
graph TD
    A[User Query] --> B[Query Analysis]
    B --> C{Query Type Detection}
    C -->|News Query| D[News Aggregator]
    C -->|General Query| E[Web Scraper]
    C -->|Deep Research| F[Deep Research Pipeline]
```

### 2. Core Components
```mermaid
graph TD
    A[Query Analysis] --> B[Intent Detection]
    A --> C[Component Extraction]
    A --> D[Search Strategy Generation]
    
    E[Web Scraper] --> F[Content Fetching]
    E --> G[Robots.txt Check]
    E --> H[Content Extraction]
    
    I[News Aggregator] --> J[Query Parsing]
    I --> K[News API Integration]
    I --> L[Date Filtering]
    
    M[Content Analyzer] --> N[Relevance Scoring]
    M --> O[Reliability Check]
    M --> P[Bias Detection]
    M --> Q[Factuality Analysis]
```

### 3. Data Flow
```mermaid
sequenceDiagram
    participant User
    participant QueryAnalyzer
    participant WebScraper
    participant NewsAggregator
    participant ContentAnalyzer
    participant RedisCache
    participant LLMClient
    
    User->>QueryAnalyzer: Submit Query
    QueryAnalyzer->>RedisCache: Check Cache
    QueryAnalyzer->>LLMClient: Analyze Query
    QueryAnalyzer->>WebScraper: Forward Query
    
    alt News Query
        WebScraper->>NewsAggregator: Process News
        NewsAggregator->>RedisCache: Store Results
    else General Query
        WebScraper->>WebScraper: Scrape Content
        WebScraper->>ContentAnalyzer: Analyze Content
        ContentAnalyzer->>RedisCache: Store Analysis
    end
    
    RedisCache->>User: Return Results
```

### 4. Component Details

#### Query Analysis (`analyzer.py`)
- Intent Detection
- Component Extraction
- Search Strategy Generation
- Source Type Identification
- Ambiguity Detection

#### Web Scraper (`webScraper.py`)
- Robots.txt Compliance
- Content Fetching
- HTML Parsing
- Content Extraction
- Rate Limiting
- Error Handling

#### News Aggregator (`newsAggregator.py`)
- Query Parsing
- News API Integration
- Date Filtering
- Result Cleaning
- Metadata Extraction

#### Content Analysis (`analyzer.py`)
- Relevance Scoring
- Reliability Assessment
- Bias Detection
- Factuality Analysis
- Recency Check

### 5. Data Storage
```mermaid
graph TD
    A[Redis Cache] --> B[Query Results]
    A --> C[Content Analysis]
    A --> D[News Articles]
    A --> E[Search Results]
```

### 6. Error Handling and Recovery
```mermaid
graph TD
    A[Error Detection] --> B{Error Type}
    B -->|API Error| C[Retry Logic]
    B -->|Content Error| D[Fallback Content]
    B -->|Cache Error| E[Direct Processing]
    C --> F[Result Compilation]
    D --> F
    E --> F
```

## Key Features

1. **Caching System**
   - Redis-based caching
   - Query result caching
   - Content analysis caching
   - News article caching

2. **Intelligent Query Processing**
   - Query intent analysis
   - Search strategy optimization
   - Component extraction
   - Source type identification

3. **Content Analysis**
   - Multi-criteria evaluation
   - Reliability scoring
   - Bias detection
   - Factuality checking

4. **News Processing**
   - Real-time news aggregation
   - Date-based filtering
   - Source verification
   - Content cleaning

5. **Error Handling**
   - Graceful degradation
   - Retry mechanisms
   - Fallback strategies
   - Error logging

## Performance Optimizations

1. **Caching Strategy**
   - Query-based caching
   - Content-based caching
   - Time-based expiration
   - Cache invalidation

2. **Concurrent Processing**
   - Async operations
   - Parallel content fetching
   - Batch processing
   - Rate limiting

3. **Resource Management**
   - Connection pooling
   - Memory optimization
   - Request throttling
   - Error recovery

## Security Measures

1. **API Security**
   - Key rotation
   - Rate limiting
   - Request validation
   - Error masking

2. **Content Security**
   - Input sanitization
   - Output encoding
   - XSS prevention
   - CSRF protection

3. **Data Protection**
   - Secure storage
   - Access control
   - Data encryption
   - Audit logging

<!-- In 
## 3. Tool Integration

### 3.1 Web Search Tool
 -->
   **Decision Making**: Results are ranked by relevance and selected for further processing based on query relevance.