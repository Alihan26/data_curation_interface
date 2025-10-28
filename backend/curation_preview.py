#!/usr/bin/env python3
import argparse
import json
import requests
from bs4 import BeautifulSoup

def fetch_html(url):
    response = requests.get(url, headers={"User-Agent": "CurationPreview/1.0"})
    response.raise_for_status()
    return response.text

def create_simple_html(entity_name, source_name, pages_data, suggestions_data):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Curation Preview - {entity_name}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
            margin: 0; 
            padding: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .header {{ 
            background: rgba(255, 255, 255, 0.95); 
            backdrop-filter: blur(10px);
            padding: 25px 30px; 
            margin: 20px; 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        .header h1 {{ 
            margin: 0 0 10px 0; 
            color: #2c3e50; 
            font-size: 2.2em; 
            font-weight: 700;
        }}
        .header p {{ 
            margin: 0; 
            color: #7f8c8d; 
            font-size: 1.1em;
        }}
        .container {{ 
            display: grid; 
            grid-template-columns: 320px 1fr 380px; 
            gap: 25px; 
            height: calc(100vh - 140px); 
            margin: 0 20px 20px 20px;
        }}
        .sidebar, .content, .right {{ 
            background: rgba(255, 255, 255, 0.95); 
            backdrop-filter: blur(10px);
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
        }}
        .sidebar h2, .content h2, .right h2 {{ 
            margin: 0 0 20px 0; 
            color: #2c3e50; 
            font-size: 1.5em; 
            font-weight: 600;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }}
        .page-item {{ 
            padding: 15px; 
            margin: 8px 0; 
            border: 2px solid #e9ecef; 
            border-radius: 10px; 
            cursor: pointer; 
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }}
        .page-item:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            border-color: #007bff;
        }}
        .page-item.active {{ 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white; 
            border-color: #0056b3;
            box-shadow: 0 8px 25px rgba(0, 123, 255, 0.3);
        }}
        .field {{ 
            margin-bottom: 25px; 
            padding: 20px; 
            border: 2px solid #e9ecef; 
            border-radius: 12px;
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            transition: all 0.3s ease;
        }}
        .field:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        .field h3 {{ 
            margin: 0 0 15px 0; 
            color: #2c3e50; 
            font-size: 1.3em;
            font-weight: 600;
        }}
        .field-value {{ 
            background: #e3f2fd; 
            padding: 10px 15px; 
            border-radius: 8px; 
            margin: 10px 0;
            border-left: 4px solid #2196f3;
            font-weight: 500;
        }}
        .confidence-badge {{ 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white; 
            padding: 5px 12px; 
            border-radius: 20px; 
            font-size: 0.9em;
            font-weight: 600;
            display: inline-block;
            margin: 5px 0;
        }}
        .btn {{ 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white; 
            border: none; 
            padding: 8px 16px; 
            margin: 5px; 
            cursor: pointer; 
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
        }}
        .btn:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
        }}
        .btn.reject {{ 
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
        }}
        .btn.reject:hover {{ 
            box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4);
        }}
        .content-text {{ 
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 25px; 
            border-radius: 12px; 
            white-space: pre-wrap; 
            max-height: 600px; 
            overflow-y: auto;
            border: 2px solid #e9ecef;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 14px; 
            line-height: 1.6;
            color: #2c3e50;
        }}
        .content-text::-webkit-scrollbar {{ width: 8px; }}
        .content-text::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 4px; }}
        .content-text::-webkit-scrollbar-thumb {{ background: #c1c1c1; border-radius: 4px; }}
        .content-text::-webkit-scrollbar-thumb:hover {{ background: #a8a8a8; }}
        .url-display {{ 
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 15px 20px; 
            border-radius: 10px; 
            margin: 20px 0;
            border-left: 4px solid #2196f3;
        }}
        .url-display a {{ 
            color: #1976d2; 
            text-decoration: none; 
            font-weight: 500;
            word-break: break-all;
        }}
        .url-display a:hover {{ 
            text-decoration: underline; 
            color: #1565c0;
        }}
        .stats {{ 
            display: flex; 
            gap: 20px; 
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .stat-item {{ 
            background: rgba(255, 255, 255, 0.8);
            padding: 15px 20px;
            border-radius: 10px;
            text-align: center;
            flex: 1;
            min-width: 120px;
        }}
        .stat-number {{ 
            font-size: 2em; 
            font-weight: 700; 
            color: #007bff; 
            margin-bottom: 5px;
        }}
        .stat-label {{ 
            color: #7f8c8d; 
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Curation Preview: {entity_name}</h1>
        <p>Source: {source_name}</p>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <h2>📄 Pages ({len(pages_data)})</h2>
            <div id="pagesList">
                {''.join([f'<div class="page-item" onclick="showPage({i})" id="page-{i}"><strong>{i+1}.</strong> {page.get("title", "Untitled")[:60]}{"..." if len(page.get("title", "")) > 60 else ""}</div>' for i, page in enumerate(pages_data)])}
            </div>
        </div>
        
        <div class="content">
            <h2>📖 Page Content</h2>
            <div id="contentDisplay">
                <div style="text-align: center; padding: 50px; color: #7f8c8d;">
                    <h3>Select a page to view content</h3>
                    <p>Click on any page in the left panel to see its content here</p>
                </div>
            </div>
        </div>
        
        <div class="right">
            <h2>🏷️ Metadata Fields</h2>
            <div id="fields">
                {''.join([f'''
                <div class="field">
                    <h3>{suggestion["field"]}</h3>
                    <div class="field-value">{suggestion.get("value", "N/A")}</div>
                    <div class="confidence-badge">{int(suggestion.get("confidence", 0) * 100)}% Confidence</div>
                    <button class="btn" onclick="acceptField(\'{suggestion["field"]}\', \'{suggestion.get("value", "")}\')">✅ Accept</button>
                    <button class="btn reject" onclick="rejectField(\'{suggestion["field"]}\', \'{suggestion.get("value", "")}\')">❌ Reject</button>
                </div>
                ''' for suggestion in suggestions_data])}
        </div>
    </div>

    <script>
        const pagesData = {json.dumps(pages_data, ensure_ascii=False)};
        
        function showPage(pageIndex) {{
            document.querySelectorAll('.page-item').forEach(item => item.classList.remove('active'));
            document.getElementById(`page-${{pageIndex}}`).classList.add('active');
            
            const page = pagesData[pageIndex];
            const contentDisplay = document.getElementById('contentDisplay');
            
            // Create stats
            const stats = `
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{len(pages_data)}</div>
                        <div class="stat-label">Total Pages</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${{page.text_content ? page.text_content.length : 0}}</div>
                        <div class="stat-label">Characters</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${{page.text_content ? page.text_content.split(' ').length : 0}}</div>
                        <div class="stat-label">Words</div>
                    </div>
                </div>
            `;
            
            contentDisplay.innerHTML = `
                <h3 style="color: #2c3e50; margin-bottom: 20px;">${{page.title || 'Untitled'}}</h3>
                <div class="url-display">
                    <strong>🔗 URL:</strong> <a href="${{page.url}}" target="_blank">${{page.url}}</a>
                </div>
                ${{stats}}
                <div class="content-text">${{page.text_content || 'No content available'}}</div>
            `;
        }}
        
        function acceptField(field, value) {{
            alert(`Accepted: ${{field}} = ${{value}}`);
        }}
        
        function rejectField(field, value) {{
            alert(`Rejected: ${{field}} = ${{value}}`);
        }}
        
        // Show first page automatically
        if (pagesData.length > 0) {{
            showPage(0);
        }}
    </script>
</body>
</html>"""
    return html

def main():
    parser = argparse.ArgumentParser(description="Build a simple curation preview HTML")
    parser.add_argument("--entity", required=True, help="Entity title")
    parser.add_argument("--source", required=True, help="Source name")
    parser.add_argument("--pages", required=True, help="Text file with URLs")
    parser.add_argument("--suggestions", required=True, help="JSON file of suggestions")
    parser.add_argument("--out", default="curation_preview.html", help="Output HTML path")
    
    args = parser.parse_args()
    
    # Read pages
    with open(args.pages, "r", encoding="utf-8") as f:
        page_urls = [line.strip() for line in f if line.strip()]
    
    # Read suggestions
    with open(args.suggestions, "r", encoding="utf-8") as f:
        suggestions_data = json.load(f)
    
    print(f"Processing {len(page_urls)} pages...")
    
    # Fetch pages
    pages_data = []
    for url in page_urls:
        try:
            print(f"Fetching: {url}")
            html = fetch_html(url)
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else url
            # Get more content and clean it up
            text_content = soup.get_text()
            # Remove excessive whitespace and clean up
            text_content = ' '.join(text_content.split())
            # Show more content (first 5000 characters)
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "...\\n\\n[Content truncated - showing first 5000 characters]"
            
            pages_data.append({
                "url": url,
                "title": title,
                "text_content": text_content
            })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            pages_data.append({
                "url": url,
                "title": f"Error: {str(e)}",
                "text_content": f"Failed to fetch: {str(e)}"
            })
    
    # Generate HTML
    html = create_simple_html(args.entity, args.source, pages_data, suggestions_data)
    
    # Write output
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Generated: {args.out}")

if __name__ == "__main__":
    main()
