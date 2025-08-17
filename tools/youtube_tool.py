"""
YouTube Tools for CrewAI Blog Automation
Optimized implementation with chunking and summarization to reduce LLM context usage
Falls back to video description when transcripts are unavailable
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, ClassVar
from collections import Counter
from pydantic import Field
from crewai.tools import BaseTool
from googleapiclient.discovery import build
from textwrap import wrap
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class YouTubeSearchTool(BaseTool):
    name: str = "YouTube Video Search"
    description: str = "Search for the latest YouTube videos on a specific topic with quality filtering"
    api_key: Optional[str] = Field(default=None, exclude=True)
    youtube: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
    def _run(self, topic: str, max_results: int = 10, days_back: int = 90) -> str:
        """
        Search for YouTube videos on a specific topic
        
        Args:
            topic: Search query/topic
            max_results: Number of videos to return (max 50)
            days_back: How many days back to search for videos
        
        Returns:
            JSON string with video information including descriptions
        """
        try:
            # Calculate date for filtering recent videos
            cutoff_date = datetime.now() - timedelta(days=days_back)
            published_after = cutoff_date.isoformat() + 'Z'
            
            # Search for videos
            search_response = self.youtube.search().list( # type: ignore
                q=topic,
                part='snippet',
                type='video',
                order='relevance',
                maxResults=min(max_results, 50),
                publishedAfter=published_after,
                videoDuration='medium',
                videoDefinition='high',
                safeSearch='moderate'
            ).execute()
            
            videos = []
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            if not video_ids:
                return json.dumps({
                    'search_query': topic,
                    'total_found': 0,
                    'search_date': datetime.now().isoformat(),
                    'videos': [],
                    'message': 'No videos found for this topic'
                })
            
            # Get additional video details
            videos_response = self.youtube.videos().list( # type: ignore
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            for item in videos_response['items']:
                # Parse duration
                duration = self._parse_duration(item['contentDetails']['duration'])
                
                # Filter for videos with substantial content (at least 5 minutes)
                if duration < 300:
                    continue
                
                # Get full description (not truncated)
                full_description = item['snippet'].get('description', '')
                
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': full_description,
                    'description_preview': full_description[:500] + '...' if len(full_description) > 500 else full_description,
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'duration_seconds': duration,
                    'duration_formatted': self._format_duration(duration),
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'video_url': f"https://www.youtube.com/watch?v={item['id']}",
                    'relevance_score': self._calculate_relevance_score(item, topic)
                }
                videos.append(video_data)
            
            # Sort by relevance score
            videos.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return json.dumps({
                'search_query': topic,
                'total_found': len(videos),
                'search_date': datetime.now().isoformat(),
                'videos': videos
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                'error': f"Error searching YouTube: {str(e)}",
                'search_query': topic
            })
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse YouTube duration format (PT#M#S) to seconds"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _format_duration(self, seconds: int) -> str:
        """Format seconds to HH:MM:SS or MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _calculate_relevance_score(self, video_item: Dict, topic: str) -> float:
        """Calculate relevance score for ranking videos"""
        score = 0.0
        
        # Title relevance (40% weight)
        title = video_item['snippet']['title'].lower()
        topic_words = topic.lower().split()
        title_matches = sum(1 for word in topic_words if word in title)
        score += (title_matches / len(topic_words)) * 40
        
        # View count factor (20% weight)
        view_count = int(video_item['statistics'].get('viewCount', 0))
        if view_count > 10000:
            score += min(20, view_count / 50000)
        
        # Engagement rate (20% weight)
        likes = int(video_item['statistics'].get('likeCount', 0))
        comments = int(video_item['statistics'].get('commentCount', 0))
        if view_count > 0:
            engagement_rate = (likes + comments * 2) / view_count
            score += min(20, engagement_rate * 1000000)
        
        # Duration preference (10% weight)
        duration = self._parse_duration(video_item['contentDetails']['duration'])
        if 600 <= duration <= 1800:  # 10-30 minutes
            score += 10
        elif 300 <= duration < 600:  # 5-10 minutes
            score += 7
        elif duration > 1800:  # > 30 minutes
            score += 5
        
        # Recency bonus (10% weight)
        published_date = datetime.fromisoformat(video_item['snippet']['publishedAt'].replace('Z', '+00:00'))
        days_old = (datetime.now().replace(tzinfo=published_date.tzinfo) - published_date).days
        if days_old <= 7:
            score += 10
        elif days_old <= 30:
            score += 5
        
        return score


class YouTubeTranscriptTool(BaseTool):
    name: str = "YouTube Full Transcript Extractor"
    description: str = "Extract complete transcript from a YouTube video and save to text file"

    # Use ClassVar for class-level constants
    OUTPUT_DIR: str = "output/transcriptions"

    def _run(self, video_id: str, video_description: str = "", language_preference: str = 'en',topic: str = "default") -> str:
        """
        Extract the FULL transcript from a YouTube video and save it to output/transcriptions.txt.
        Returns simple status information.
        """
        transcript_file = f"output/transcriptions/transcript_{topic}.txt"

        try:
            full_text = ""
            source_type = ""
            language_code = language_preference
            
            try:
                # Initialize YouTubeTranscriptApi and get transcript list
                ytt_api = YouTubeTranscriptApi()
                transcript_list = ytt_api.list(video_id)

                # Try to find transcript in preferred language
                try:
                    transcript = transcript_list.find_transcript([language_preference])
                    fetched_transcript = transcript.fetch()
                    source_type = "manual" if not transcript.is_generated else "auto-generated"
                    transcript_data = fetched_transcript.to_raw_data()
                    language_code = getattr(transcript, "language_code", language_preference)
                except:
                    # Fallback to any available English transcript
                    languages = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
                    transcript = transcript_list.find_generated_transcript(languages)
                    fetched_transcript = transcript.fetch()
                    transcript_data = fetched_transcript.to_raw_data()
                    source_type = "auto-generated"
                    language_code = getattr(transcript, "language_code", "en")

                # Extract raw full text
                full_text = ' '.join([item.get('text', '') for item in transcript_data]).strip()
                
                # Clean up the text slightly (remove bracketed annotations)
                full_text = re.sub(r'\[\s*.*?\s*\]', '', full_text)
                full_text = re.sub(r'\s+', ' ', full_text).strip()

            except (TranscriptsDisabled, NoTranscriptFound, Exception):
                # Fallback: use video description if no transcript available
                full_text = video_description or "(No transcript or description available)"
                source_type = "description-fallback"
                language_code = "n/a"

            # Save the full transcript
            self._save_full_transcript(
                video_id=video_id,
                full_text=full_text,
                language_code=language_code,
                source_type=source_type,
                file_path=transcript_file.format(topic=topic)
            )

            # Return simple status
            word_count = len(full_text.split()) if full_text else 0
            return json.dumps({
                'video_id': video_id,
                'status': 'success',
                'source_type': source_type,
                'language': language_code,
                'word_count': word_count,
                'saved_to': transcript_file.format(topic=topic),
                'timestamp': datetime.now().isoformat()
            }, indent=2)

        except Exception as e:
            # Final fallback on any other error
            fallback_text = f"(Error occurred) {str(e)}\n\n{video_description or ''}".strip()
            self._save_full_transcript(
                video_id=video_id,
                full_text=fallback_text,
                language_code="n/a",
                source_type="error-fallback",
                file_path=transcript_file.format(topic=topic)
            )
            return json.dumps({
                'video_id': video_id,
                'status': 'error',
                'error': str(e),
                'source_type': 'error-fallback',
                'saved_to': transcript_file.format(topic=topic),
                'timestamp': datetime.now().isoformat()
            })

    def _save_full_transcript(self, video_id: str, full_text: str, language_code: str, source_type: str,file_path: str) -> None:
        """
        Append the full transcript to output/transcriptions.txt with clear delimiters.
        Splits transcript into smaller chunks for better RAG indexing.
        """
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)         
        timestamp = datetime.now().isoformat()
        header = [
            "===== BEGIN TRANSCRIPT =====",
            f"Video ID: {video_id}",
            f"Language: {language_code}",
            f"Source: {source_type}",
            f"Saved At: {timestamp}",
            ""
        ]
        footer = ["", "===== END TRANSCRIPT =====", ""]

        # 🔑 Split transcript into smaller chunks (e.g., 400 characters per line)
        chunks = wrap(full_text, width=400)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\n".join(header))
            for chunk in chunks:
                f.write(chunk.strip() + "\n")
            f.write("\n".join(footer) + "\n")