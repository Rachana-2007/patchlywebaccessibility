"""
Patchly - Video Subtitle & Caption Auditor
Compliant with WCAG 2.1 Success Criterion 1.2.2 (Captions - Prerecorded - Level A)
"""

from typing import Dict, Any, Optional
from bs4 import Tag

def audit_video_tag(video_tag: Tag, index: int) -> Optional[Dict[str, Any]]:
    """
    Audits a <video> element to ensure it contains captions or subtitle tracks.
    Returns issue dict if violation found, else None.
    """
    # Check for <track> children
    tracks = video_tag.find_all('track')
    has_captions = False

    for track in tracks:
        kind = track.get('kind', '').lower()
        src = track.get('src', '').strip()
        # WCAG 1.2.2 requires captions or subtitles
        if kind in ['captions', 'subtitles'] and src:
            has_captions = True
            break

    if not has_captions:
        # Check if video has audio disabled or autoplay muted
        is_muted = video_tag.has_attr('muted')
        
        poster = video_tag.get('poster', '')
        poster_preview = f' poster="{poster}"' if poster else ''

        quick_fix = (
            f'<video controls{poster_preview}>\n'
            f'  <source src="..." type="video/mp4">\n'
            f'  <track kind="captions" src="subtitles_en.vtt" srclang="en" label="English Captions" default>\n'
            f'</video>'
        )

        return {
            "rule_id": "video-captions-missing",
            "wcag_sc": "1.2.2 Captions (Prerecorded) (Level A)",
            "severity": "SERIOUS",
            "title": "Video Lacks Captions or Subtitles Track",
            "element_tag": "video",
            "element_html": str(video_tag)[:200] + "...",
            "description": "The video element has no <track kind='captions'> or subtitles. Deaf and hard-of-hearing individuals cannot access spoken audio.",
            "quick_fix_code": quick_fix,
            "suggested_action": "Add a WebVTT (.vtt) caption track using <track kind='captions' src='...'>."
        }

    return None
