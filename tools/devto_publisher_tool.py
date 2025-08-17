# tools/devto_publisher_tool.py
import os
import json
import requests
from typing import Optional
from crewai.tools import BaseTool
from pydantic import Field
from dotenv import load_dotenv
load_dotenv()

class DevToPublisherTool(BaseTool):
    name: str = "Dev.to Publisher"
    description: str = "Publish blog posts directly to Dev.to platform"
    
    api_key: Optional[str] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv('DEVTO_API_KEY')
    
    def _run(self, markdown_content: str, published: bool = True) -> str:
        """
        Publish markdown content to Dev.to - Simple approach
        """
        if not self.api_key:
            return json.dumps({
                'success': False,
                'error': 'DEVTO_API_KEY not found'
            })
        
        try:
            # Extract basic info from markdown
            title = self._extract_title(markdown_content)
            tags = self._extract_tags(markdown_content) 
            cover_image = self._extract_cover_image(markdown_content)
            
            # Clean content (remove frontmatter if present)
            clean_content = self._clean_content(markdown_content)
            
            # Simple API payload
            article_data = {
                "article": {
                    "title": title,
                    "body_markdown": clean_content,
                    "published": published,
                    "tags": tags[:4]  # Max 4 tags
                }
            }
            
            if cover_image:
                article_data['article']['main_image'] = cover_image
            
            # Publish to Dev.to
            response = requests.post(
                "https://dev.to/api/articles",
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json=article_data,
                timeout=30
            )
            
            if response.status_code == 201:
                article = response.json()
                return json.dumps({
                    'success': True,
                    'url': article.get('url', ''),
                    'id': article.get('id'),
                    'message': 'Successfully published to Dev.to!'
                })
            else:
                return json.dumps({
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'details': response.text[:200]
                })
        
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    def _extract_title(self, content: str) -> str:
        """Extract title from frontmatter or first H1"""
        # Try frontmatter first
        if 'title:' in content:
            for line in content.split('\n'):
                if line.strip().startswith('title:'):
                    return line.split(':', 1)[1].strip().strip('"\'')
        
        # Fallback to first H1
        for line in content.split('\n'):
            if line.startswith('# '):
                return line[2:].strip()
        
        return "Untitled Post"
    
    def _extract_tags(self, content: str) -> list:
        """Extract and clean tags from frontmatter"""
        if 'tags:' in content:
            for line in content.split('\n'):
                if line.strip().startswith('tags:'):
                    tags_str = line.split(':', 1)[1].strip()
                    if tags_str.startswith('[') and tags_str.endswith(']'):
                        tags_str = tags_str[1:-1]
                        raw_tags = [tag.strip().strip('"\'') for tag in tags_str.split(',')]
                        # Clean tags: remove non-alphanumeric characters
                        import re
                        cleaned_tags = [re.sub(r'[^a-zA-Z0-9]', '', tag).lower() 
                                    for tag in raw_tags if tag.strip()]
                        return cleaned_tags[:5]  # Max 4 tags
        return []

    
    def _extract_cover_image(self, content: str) -> str:
        """Extract cover image URL from frontmatter"""
        if 'cover_image:' in content:
            for line in content.split('\n'):
                if line.strip().startswith('cover_image:'):
                    return line.split(':', 1)[1].strip().strip('"\'')
        return ""
    
    def _clean_content(self, content: str) -> str:
        """Remove YAML frontmatter and return clean markdown"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()  # Return content after frontmatter
        return content

# Create tool instance
devto_publisher_tool = DevToPublisherTool()
