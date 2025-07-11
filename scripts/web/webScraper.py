import os
import asyncio
import aiohttp
import tiktoken
import requests
import logging
import urllib.robotparser
# from pyppeteer import launch
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from config.llmClient import client
from config.redis import get_stream_data_from_redis, store_stream_data_in_redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SERPER_SEARCH_ENDPOINT = "https://google.serper.dev/search"

SERPER_API_KEYS = [
    os.getenv("SERPER_API_KEY_1"),
    # os.getenv("SERPER_API_KEY_2"),
    # os.getenv("SERPER_API_KEY_3"),
    # os.getenv("SERPER_API_KEY_4"),
    # os.getenv("SERPER_API_KEY_5"),
    # os.getenv("SERPER_API_KEY_6"),
    # os.getenv("SERPER_API_KEY_7"),
]
serperKeyIndex = 0


def _get_next_serper_key():
    """
    Retrieve the next API key from the list of Serper API keys in a round-robin fashion.

    Returns:
        str: The next API key to be used.
    """
    global serperKeyIndex
    key = SERPER_API_KEYS[serperKeyIndex]
    serperKeyIndex = (serperKeyIndex + 1) % len(SERPER_API_KEYS)
    return key


# Create a cache for robots.txt parsers to avoid repeated fetches
robots_txt_cache = {}

async def _check_robots_permission(url):
    """
    Check if scraping is allowed for this URL according to robots.txt.
    
    Args:
        url (str): The URL to check.
        
    Returns:
        bool: True if scraping is allowed, False otherwise.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"
        
        # Check if we've already parsed this robots.txt
        if base_url in robots_txt_cache:
            rp = robots_txt_cache[base_url]
        else:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            headers = {"User-Agent": "ResearchBot/1.0"}
            
            # Fetch and parse the robots.txt file
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(robots_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            # RobotFileParser expects a list of strings
                            rp.parse(robots_content.splitlines())
                        else:
                            # If robots.txt doesn't exist or can't be accessed, assume we can crawl
                            return True
                except Exception as e:
                    print(f"Error fetching robots.txt for {base_url}: {e}")
                    return True
            
            # Cache the parser
            robots_txt_cache[base_url] = rp
        
        # Check if our bot can fetch this URL
        for bot in ["ResearchBot", "*"]:
            if rp.can_fetch(bot, url):
                return True
        return False
    
    except Exception as e:
        print(f"Error checking robots.txt permissions: {e}")
        # If there's an error checking, be conservative and assume we can't fetch
        return False

async def _fetch_content(session, url):
    """
    Fetch the HTML content of a given URL asynchronously, respecting robots.txt.

    Args:
        session (aiohttp.ClientSession): The aiohttp session object for making requests.
        url (str): The URL to fetch content from.

    Returns:
        str or None: The HTML content of the URL if successful, otherwise None.
    """
    timeout_seconds = 2

    # Check robots.txt first
    is_allowed = await _check_robots_permission(url)
    if not is_allowed:
        print(f"Skipping {url} - disallowed by robots.txt")
        return None
    
    try:
        async with session.get(url,timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as response:
            if response.status == 200:
                html = await response.text()
                return html
            else:
                return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


async def _extract_relevant_data(html):
    """
    Extract relevant text content such as paragraphs and headings from the provided HTML.

    Args:
        html (str): The HTML content to parse.

    Returns:
        str or None: A string containing the extracted text, or None if an error occurs.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        content = []
        for tag in soup.find_all(["p","span", "h1", "h2", "h3", "h4", "h5", "h6", "div"]):
            text = tag.get_text(strip=True)
            if tag.name == "div" and list(tag.children):
                continue
            if text:
                content.append(text)
        return " ".join(content)
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None


async def _process_dict(item, session):
    """
    Process a dictionary by fetching and extracting content from its URL.

    Args:
        item (dict): A dictionary containing a "url" key.
        session (aiohttp.ClientSession): The aiohttp session object for making requests.

    Returns:
        dict: The input dictionary updated with a "content" key containing extracted text or None.
    """
    url = item.get("url")
    if not url:
        item["content"] = None
        return item

    html = await _fetch_content(session, url)
    if html:
        content = await _extract_relevant_data(html)
        item["content (truncated)"] = content[:1000] if isinstance(content, str) else content
    else:
        item["content"] = None

    return item


async def _scrape_urls(data):
    """
    Process a list of dictionaries containing URLs and fetch their content asynchronously.

    Args:
        data (list): A list of dictionaries, each with a "url" key.

    Returns:
        list: A list of dictionaries with an additional "content" key containing extracted text.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [_process_dict(item, session) for item in data]
        results = await asyncio.gather(*tasks)
    return results


async def _search_with_serper(query: str, shallow: bool = True):
    """
    Perform a search using the Serper API and optionally scrape additional content from the results.

    Args:
        query (str): The search query.
        shallow (bool): Whether to perform shallow searches or scrape additional content.

    Returns:
        dict: A dictionary containing search contexts, top stories, related searches, and images.
    """
    api_key = _get_next_serper_key()

    payload = {"q": query, "num": 10}
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                SERPER_SEARCH_ENDPOINT, json=payload, headers=headers
            ) as response:
                if response.status == 200:
                    json_content = await response.json()
                    contexts = []
                    stories, related_searches, images = None, None, None

                    if "knowledgeGraph" in json_content:
                        url = json_content["knowledgeGraph"].get(
                            "descriptionUrl"
                        ) or json_content["knowledgeGraph"].get("website")
                        snippet = json_content["knowledgeGraph"].get("description")
                        if url and snippet:
                            contexts.append(
                                {
                                    "name": json_content["knowledgeGraph"].get(
                                        "title", ""
                                    ),
                                    "url": url,
                                    "snippet": snippet,
                                }
                            )

                    if "answerBox" in json_content:
                        url = json_content["answerBox"].get("url")
                        snippet = json_content["answerBox"].get(
                            "snippet"
                        ) or json_content["answerBox"].get("answer")
                        if url and snippet:
                            contexts.append(
                                {
                                    "name": json_content["answerBox"].get("title", ""),
                                    "url": url,
                                    "snippet": snippet,
                                }
                            )

                    contexts.extend(
                        {
                            "name": c["title"],
                            "url": c["link"],
                            "snippet": c.get("snippet", ""),
                        }
                        for c in json_content.get("organic", [])
                    )

                    if not shallow:
                        await _scrape_urls(contexts)

                    if "topStories" in json_content:
                        stories = json_content["topStories"]

                    if "relatedSearches" in json_content:
                        related_searches = json_content["relatedSearches"]

                    if "images" in json_content:
                        images = json_content["images"]

                    return {
                        "contexts": contexts,
                        "stories": stories,
                        "relatedSearches": related_searches,
                        "images": images,
                    }
                else:
                    print(f"Error: Received status code {response.status}")
                    return []
        except Exception as e:
            print(f"Error encountered: {e}")
            return []


async def search_web(user_google_id:str, query: str):
    """
    Perform a shallow search using the Serper API without additional content scraping.

    Args:
        query (str): The search query.

    Returns:
        dict: A dictionary containing search contexts, top stories, related searches, and images.
    """
    return await _search_with_serper(query=query, shallow=True)


async def read_webpage(user_google_id: str, url: str):
    """
    Perform a deep scrape of a specific website URL to extract relevant content.
    
    Args:
        url (str): The URL of the website to scrape
        
    Returns:
        dict: A dictionary containing the extracted content, metadata, and status
    """
    async with aiohttp.ClientSession() as session:
        try:
            html = await _fetch_content(session, url)
            if not html:
                return {
                    "status": "error",
                    "message": f"Failed to fetch content from {url}",
                    "content": None,
                    "metadata": None
                }
            
            # Parse the HTML content
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract metadata
            metadata = {
                "title": soup.title.string if soup.title else None,
                "url": url,
            }
            
            # Extract structured content
            structured_content = {
                "main_text": await _extract_relevant_data(html),
                "headings": [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])],
                "links": [{"text": a.get_text(strip=True), "href": a.get("href")} 
                         for a in soup.find_all("a") if a.get("href") and a.get_text(strip=True)][:10],
            }
            
            # Extract any tables if present
            tables = []
            for table in soup.find_all("table"):
                table_data = []
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:  # Skip empty rows
                        table_data.append(row_data)
                if table_data:
                    tables.append(table_data)
            
            structured_content["tables"] = tables
            
            return {
                "status": "success",
                "message": f"Successfully scraped content from {url}",
                "content": structured_content,
                "metadata": metadata
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error scraping {url}: {str(e)}",
                "content": None,
                "metadata": None
            }

async def scrape_webpage(user_google_id: str, url: str, timeout: int = 10, selector_query: str = ""):
    """
    Scrape a webpage using HTTP requests and BeautifulSoup (without a browser),
    convert the HTML content to markdown, split it into manageable chunks, and
    summarize it using an LLM, with Redis caching to improve efficiency.

    Args:
        user_google_id (str): The unique Google ID of the user requesting the scrape.
        url (str): The URL of the webpage to scrape.
        timeout (int, optional): Timeout for the HTTP request in seconds. Defaults to 10.
        selector_query (str, optional): A selector-based query to focus the summarization on. Defaults to "".

    Returns:
        dict: A dictionary containing:
            - status (str): The result status ("success" or "error").
            - message (str): A descriptive message about the process outcome.
            - summarized_content (str or None): The summarized markdown content, if successful.
            - metadata (dict or None): Metadata including page title and URL.
    """
    
    
    logger = logging.getLogger(__name__.rsplit('.', 1)[0])
    
    stream_id = f"{user_google_id}:{url}"
    
    # Check if cached data exists
    try:
        cached_data = await get_stream_data_from_redis(stream_id)
        if cached_data:
            logger.info(f"Using cached data for {url}")
            pages = cached_data.get("pages", [])
            metadata = cached_data.get("metadata", {})
            
            # Skip to summarization with cached content
            return await summarize_pages(pages, metadata, url, selector_query)
    except Exception as redis_err:
        logger.error(f"Error accessing Redis cache: {str(redis_err)}")
        cached_data = None
    
    # Use requests instead of pyppeteer
    try:
        logger.info(f"Fetching {url} with requests")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        logger.info(f"Successfully fetched {url} with status code {response.status_code}")
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "Untitled Page"
        
        # Convert to markdown
        html_content = str(soup)
        markdown_content = md(html_content)
        
        logger.info(f"Successfully converted HTML to markdown for {url}")
        
        # Tokenize and split content
        try:
            encoder = tiktoken.get_encoding("o200k_base")
            tokens = encoder.encode(markdown_content)
            chunk_size = 10000
            pages = [
                encoder.decode(tokens[i:i + chunk_size])
                for i in range(0, len(tokens), chunk_size)
            ]
            logger.info(f"Split content into {len(pages)} chunks for {url}")
        except Exception as token_err:
            logger.error(f"Error tokenizing content: {str(token_err)}")
            # Fallback to simple text splitting if tokenization fails
            pages = [markdown_content]
        
        metadata = {"title": title, "url": url}
        
        # Cache the pages and metadata in Redis
        try:
            cache_payload = {
                "pages": pages,
                "metadata": metadata
            }
            await store_stream_data_in_redis(stream_id, cache_payload)
            logger.info(f"Successfully cached content from {url}")
        except Exception as cache_err:
            logger.warning(f"Failed to cache content from {url}: {str(cache_err)}")
        
        # Process the pages for summarization
        return await summarize_pages(pages, metadata, url, selector_query)
        
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error for {url}: {str(req_err)}")
        return {
            "status": "error",
            "message": f"Error fetching {url}: {str(req_err)}",
            "summarized_content": None,
            "metadata": None
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error scraping {url}: {str(e)}",
            "summarized_content": None,
            "metadata": None
        }

async def summarize_pages(pages, metadata, url, selector_query=""):
    """
    Summarize a list of markdown content chunks using an LLM,
    optionally aggregating multiple chunk summaries into a final summary.

    Args:
        pages (List[str]): A list of markdown text chunks representing the page content.
        metadata (dict): Metadata associated with the content (e.g., title, URL).
        url (str): The URL from which the content was scraped.
        selector_query (str, optional): A query to focus the summarization on specific content. Defaults to "".

    Returns:
        dict: A dictionary containing:
            - status (str): The result status ("success" or "error").
            - message (str): A message describing the result.
            - summarized_content (str): The final summarized content.
            - metadata (dict): The provided metadata passed through.
    """
    import logging
    
    logger = logging.getLogger(__name__.rsplit('.', 1)[0])
    
    # Skip summarization if no content was retrieved
    if not pages or all(not page.strip() for page in pages):
        return {
            "status": "error",
            "message": f"No content retrieved from {url}",
            "summarized_content": None,
            "metadata": metadata
        }

    # Summarize each chunk using the "gpt-4o-mini" model
    chunk_summaries = []
    for i, chunk in enumerate(pages):
        system_prompt = (
            "You are a helpful assistant that extracts and summarizes the content provided in markdown format. "
            "Summary should be of appropriate length to encompass most of the content."
        )
        if selector_query:
            system_prompt += f" Focus on the following aspect: {selector_query}."
        else:
            system_prompt += " Summarize the content comprehensively."
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Content (chunk {i+1} of {len(pages)}): {chunk}"}
        ]
        
        try:
            response = await client.generate_data_with_llm(
                messages=messages, 
                model="gpt-4o-mini", 
                temperature=0.2
            )
            
            # Convert to dict and check for valid response
            response_dict = response.to_dict()
            if (response_dict.get("choices") and 
                response_dict["choices"][0].get("finish_reason") == "stop" and
                response_dict["choices"][0].get("message", {}).get("content")):
                summary = response_dict["choices"][0]["message"]["content"]
                logger.info(f"Successfully summarized chunk {i+1} of {len(pages)} for {url}")
            else:
                summary = f"Summary not completed for chunk {i+1}."
                logger.warning(f"Incomplete summary for {url}, chunk {i+1}")
                
        except Exception as llm_err:
            logger.error(f"Error during summarization for {url}, chunk {i+1}: {str(llm_err)}")
            summary = f"Error summarizing chunk {i+1}: {str(llm_err)}"
            
        chunk_summaries.append(summary)

    # If more than one chunk, aggregate individual summaries
    if len(chunk_summaries) > 1:
        aggregated_content = "\n\n".join(chunk_summaries)
        aggregation_prompt = (
            "You are a helpful assistant that aggregates multiple summaries into a final concise summary."
        )
        messages = [
            {"role": "system", "content": aggregation_prompt},
            {"role": "user", "content": f"Summaries from {url}: {aggregated_content}"}
        ]
        
        try:
            agg_response = await client.generate_data_with_llm(
                messages=messages, 
                model="gpt-4o-mini", 
                temperature=0.2
            )
            
            # Convert to dict and check for valid response
            agg_response_dict = agg_response.to_dict()
            if (agg_response_dict.get("choices") and 
                agg_response_dict["choices"][0].get("finish_reason") == "stop" and
                agg_response_dict["choices"][0].get("message", {}).get("content")):
                final_summary = agg_response_dict["choices"][0]["message"]["content"]
                logger.info(f"Successfully aggregated summaries for {url}")
            else:
                logger.warning(f"Incomplete aggregated summary for {url}")
                final_summary = aggregated_content
                
        except Exception as agg_err:
            logger.error(f"Error during aggregation for {url}: {str(agg_err)}")
            final_summary = aggregated_content
    else:
        final_summary = chunk_summaries[0] if chunk_summaries else ""

    return {
        "status": "success",
        "message": f"Successfully summarized content from {url}.",
        "summarized_content": final_summary,
        "metadata": metadata
    }


# Previous using headless browser

# async def scrape_webpage(user_google_id: str, url: str, timeout: int = 10, selector_query: str = ""):
#     """
#     Scrape a webpage using a headless browser, convert the content to markdown,
#     and split it into chunks of roughly 10,000 tokens. Each chunk is then passed to the
#     "gpt-4o-mini" model (with an optional selector query) for summarization.
#     If the content spans multiple chunks, the individual summaries are aggregated into a 
#     final concise summary. The scraped markdown pages and metadata are cached in Redis for 
#     faster re-access.

#     Args:
#         user_google_id (str): User identifier used for caching.
#         url (str): The URL of the webpage to scrape (must include http:// or https://).
#         timeout (int, optional): Maximum number of seconds to wait for page loading (default 10 seconds).
#         selector_query (str, optional): A query defining which section to focus on when summarizing.

#     Returns:
#         dict: A dictionary containing:
#             - status (str): "success" or "error".
#             - message (str): Informational message.
#             - summarized_content (str or None): The final summarized text of the webpage.
#             - metadata (dict or None): Metadata such as title and URL.
#     """
#     stream_id = f"{user_google_id}:{url}"

#     # Check if markdown pages and metadata are cached.
#     cached_data = await get_stream_data_from_redis(stream_id)
#     if cached_data:
#         pages = cached_data.get("pages", [])
#         metadata = cached_data.get("metadata", {})
#     else:
#         browser = None
#         try:
#             browser = await launch(headless=True, args=['--no-sandbox'])
#             page = await browser.newPage()
#             try:
#                 await asyncio.wait_for(page.goto(url), timeout=timeout)
#             except asyncio.TimeoutError:
#                 print(f"Timeout reached while loading {url}. Proceeding with available content.")

#             # Get HTML content and page title.
#             html_content = await page.content()
#             title = await page.title() or None

#             # Convert HTML to Markdown using markdownify.
#             markdown_content = md(html_content)

#             # Tokenize and split the markdown into chunks of ~10,000 tokens.
#             encoder = tiktoken.get_encoding("o200k_base")
#             tokens = encoder.encode(markdown_content)
#             chunk_size = 50000
#             pages = [
#                 encoder.decode(tokens[i:i + chunk_size])
#                 for i in range(0, len(tokens), chunk_size)
#             ]

#             metadata = {"title": title, "url": url}

#             # Cache the pages and metadata in Redis.
#             cache_payload = {
#                 "pages": pages,
#                 "metadata": metadata
#             }
#             await store_stream_data_in_redis(stream_id, cache_payload)
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Error scraping {url}: {str(e)}",
#                 "summarized_content": None,
#                 "metadata": None
#             }
#         finally:
#             if browser:
#                 await browser.close()
#             print("Fetched page content.")

#     # Summarize each chunk using the "gpt-4o-mini" model.
#     chunk_summaries = []
#     for chunk in pages:
#         system_prompt = (
#             "You are a helpful assistant that extracts and summarizes the content provided in markdown format. Summary should be of appropriate length to emcompass most of the content."
#         )
#         if selector_query:
#             system_prompt += f" Focus on the following aspect: {selector_query}."
#         else:
#             system_prompt += " Summarize the content comprehensively."
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": "Content: " + chunk}
#         ]
#         try:
#             response = (
#                 await client.generate_data_with_llm(
#                     messages=messages, 
#                     model="gpt-4o-mini", 
#                     temperature=0.2
#                 )
#             ).to_dict()
#             if response["choices"][0]["finish_reason"] == "stop":
#                 summary = response["choices"][0]["message"]["content"]
#             else:
#                 summary = "Summary not completed."
#         except Exception as llm_err:
#             return {
#                 "status": "error",
#                 "message": f"Error during summarization: {str(llm_err)}",
#                 "summarized_content": None,
#                 "metadata": cached_data.get("metadata") if cached_data else None
#             }
#         chunk_summaries.append(summary)

#     # If more than one chunk, aggregate individual summaries.
#     if len(chunk_summaries) > 1:
#         aggregated_content = "\n\n".join(chunk_summaries)
#         aggregation_prompt = (
#             "You are a helpful assistant that aggregates multiple summaries into a final concise summary."
#         )
#         messages = [
#             {"role": "system", "content": aggregation_prompt},
#             {"role": "user", "content": "Summaries: " + aggregated_content}
#         ]
#         try:
#             agg_response = (
#                 await client.generate_data_with_llm(
#                     messages=messages, 
#                     model="gpt-4o-mini", 
#                     temperature=0.2
#                 )
#             ).to_dict()
#             if agg_response["choices"][0]["finish_reason"] == "stop":
#                 final_summary = agg_response["choices"][0]["message"]["content"]
#             else:
#                 final_summary = aggregated_content
#         except Exception as agg_err:
#             final_summary = aggregated_content
#     else:
#         final_summary = chunk_summaries[0] if chunk_summaries else ""

#     return {
#         "status": "success",
#         "message": f"Successfully summarized content from {url}.",
#         "summarized_content": final_summary,
#         "metadata": cached_data.get("metadata") if cached_data else metadata
#     }