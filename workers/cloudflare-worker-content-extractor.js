import { JSDOM } from 'jsdom';
import { parse } from 'date-fns';
import { format } from 'date-fns';

class HTMLContentExtractor {
  constructor() {
    this.datePatterns = [
      /\d{1,2}\/\d{1,2}\/\d{4}/,  // MM/DD/YYYY or DD/MM/YYYY
      /\d{4}-\d{2}-\d{2}/,      // YYYY-MM-DD
      /\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}/,  // DD Mon YYYY
    ];
  }

  async extractContent(url) {
    const response = await fetch(url);
    const html = await response.text();
    const dom = new JSDOM(html);
    const document = dom.window.document;

    const title = document.title || "";
    const author = this._extractAuthor(document);
    const date = this._extractDate(document);
    const mainContent = this._extractMainContent(document, url);

    return {
      title,
      author,
      date,
      content: mainContent
    };
  }

  _extractAuthor(document) {
    const authorMeta = document.querySelector('meta[name="author"]');
    if (authorMeta) {
      return authorMeta.getAttribute('content');
    }

    const authorElements = document.querySelectorAll('[class*="author"]');
    for (const element of authorElements) {
      return element.textContent.trim();
    }

    return "";
  }

  _extractDate(document) {
    const dateMeta = 
      document.querySelector('meta[property="article:published_time"]') ||
      document.querySelector('meta[name="pubdate"]') ||
      document.querySelector('meta[name="date"]');

    if (dateMeta) {
      return this._parseAndFormatDate(dateMeta.getAttribute('content'));
    }

    const fullText = document.body.textContent;
    for (const pattern of this.datePatterns) {
      const match = fullText.match(pattern);
      if (match) {
        return this._parseAndFormatDate(match[0]);
      }
    }

    const dateElements = document.querySelectorAll('[class*="date"]');
    for (const element of dateElements) {
      const parsedDate = this._parseAndFormatDate(element.textContent.trim());
      if (parsedDate) {
        return parsedDate;
      }
    }

    return "";
  }

  _parseAndFormatDate(dateStr) {
    try {
      const parsedDate = parse(dateStr, 'yyyy-MM-dd', new Date());
      return format(parsedDate, 'yyyy-MM-dd');
    } catch (error) {
      return null;
    }
  }

  _extractMainContent(document, baseUrl) {
    // Remove scripts and styles
    document.querySelectorAll('script, style').forEach(el => el.remove());

    // Remove navigation elements
    document.querySelectorAll('nav, header, footer').forEach(el => el.remove());

    // Try to find the main content area
    const mainContentArea = 
      document.querySelector('article') || 
      document.querySelector('main') || 
      document.querySelector('.content') || 
      document.body;

    return this._extractStructuredContent(mainContentArea, baseUrl);
  }

  _extractStructuredContent(element, baseUrl, level = 0) {
    if (!element) return "";

    let content = "";

    if (element.nodeType === Node.TEXT_NODE) {
      return element.textContent.trim() + "\n";
    }

    const tagName = element.tagName.toLowerCase();

    if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
      const headerLevel = parseInt(tagName[1]) + level;
      return "#".repeat(headerLevel) + " " + element.textContent.trim() + "\n\n";
    } else if (tagName === 'p') {
      content = element.textContent.trim() + "\n\n";
      const img = element.querySelector('img');
      if (img) {
        content += this._extractImage(img, baseUrl);
      }
      return content;
    } else if (['ul', 'ol'].includes(tagName)) {
      for (const li of element.querySelectorAll('li')) {
        content += "  ".repeat(level) + "- " + li.textContent.trim() + "\n";
      }
      return content + "\n";
    } else if (tagName === 'blockquote') {
      return "> " + element.textContent.trim() + "\n\n";
    } else if (tagName === 'img') {
      return this._extractImage(element, baseUrl);
    } else if (['pre', 'code'].includes(tagName)) {
      return "```\n" + element.textContent.trim() + "\n```\n\n";
    }

    for (const child of element.childNodes) {
      content += this._extractStructuredContent(child, baseUrl, level);
    }

    return content;
  }

  _extractImage(img, baseUrl) {
    const src = img.getAttribute('src');
    if (src) {
      const fullUrl = new URL(src, baseUrl).href;
      const alt = img.getAttribute('alt') || '';
      return `![${alt}](${fullUrl})\n\n`;
    }
    return "";
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const targetUrl = url.searchParams.get('url');

    if (!targetUrl) {
      return new Response('Please provide a URL to extract content from', { status: 400 });
    }

    const extractor = new HTMLContentExtractor();

    try {
      const extractedContent = await extractor.extractContent(targetUrl);
      const markdown = formatAsMarkdown(extractedContent);
      return new Response(markdown, {
        headers: { 'Content-Type': 'text/markdown' },
      });
    } catch (error) {
      return new Response(`Error extracting content: ${error.message}`, { status: 500 });
    }
  },
};

function formatAsMarkdown(extractedContent) {
  let md = `# ${extractedContent.title}\n\n`;
  
  if (extractedContent.author) {
    md += `**Author:** ${extractedContent.author}\n\n`;
  }
  
  if (extractedContent.date) {
    md += `**Date:** ${extractedContent.date}\n\n`;
  }
  
  md += extractedContent.content;
  
  return md;
}

// example
// https://your-worker.your-subdomain.workers.dev/?url=https://example.com/article