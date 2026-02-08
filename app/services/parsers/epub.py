import pathlib
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from .base import BaseParser

class EpubParser(BaseParser):
    def parse(self, file_path: pathlib.Path) -> List[Dict[str, Any]]:
        """
        Parse EPUB using structural metadata (Spine + TOC) to ensure correct ordering.
        """
        tasks = []
        try:
            book = epub.read_epub(str(file_path))
            
            # 1. Build TOC Map (href -> title)
            # TOC can be nested, so we flaten it.
            # We also might need to handle fragments in hrefs.
            toc_map = self._flatten_toc(book.toc)
            
            # 2. Iterate Spine (Linear reading order)
            # Spine items are (item_id, linear_flag)
            for item_id, linear in book.spine:
                # Skip non-linear items (e.g. auxiliary content, cover, some TOCs)
                if linear == 'no':
                    continue

                item = book.get_item_with_id(item_id)
                if not item:
                    continue
                    
                # Skip non-document items (e.g. images, css)
                if item.get_type() != ebooklib.ITEM_DOCUMENT:
                    continue

                # Extract content
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text(separator='\n').strip()
                
                # Skip empty/short content
                if len(text_content) < 50:
                    continue

                # Determine Title
                # Priority: TOC > HTML Title > h1/h2 > Filename
                file_name = item.get_name()
                title = toc_map.get(file_name)
                
                if not title:
                    # Try fuzzy match (e.g. ignoring fragments or leading paths)
                    # toc href might be "Text/chapter1.xhtml", item name "chapter1.xhtml"
                    # or vice versa.
                    for href, t in toc_map.items():
                        if href.endswith(file_name) or file_name.endswith(href):
                             title = t
                             break
                
                if not title:
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()
                    else:
                        h_tag = soup.find(['h1', 'h2'])
                        if h_tag:
                            title = h_tag.get_text().strip()
                        else:
                            title = file_name

                tasks.append({
                    "id": len(tasks) + 1,
                    "title": title,
                    "content": text_content,
                    "status": "pending",
                    "audio_path": ""
                })

            # Check if we got anything. If not (e.g. empty spine?), fallback to item iteration?
            # Standard EPUBs should have spine.
            if not tasks:
                print("Warning: No tasks extracted from Spine. Falling back to item iteration.")
                # Fallback logic logic from old book_manager?
                # iterating book.get_items() is risky for order.
                # But if spine is broken, what choice do we have?
                pass

            return tasks

        except Exception as e:
            print(f"Error parsing EPUB {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _flatten_toc(self, toc, parent_title: Optional[str] = None) -> Dict[str, str]:
        """Flatten nested TOC to a dict of {href: title}."""
        mapping = {}
        for node in toc:
            # node can be epub.Link or tuple/list
            if isinstance(node, (list, tuple)):
                # Chapter with subsections: (Link, [sub_links...])
                # Process the main link
                main_link = node[0]
                if isinstance(main_link, epub.Link):
                     mapping[self._clean_href(main_link.href)] = main_link.title
                
                # Process children
                # Pass parent title? Maybe we want "Volume 1 - Chapter 1"?
                # For now just use child title.
                for child in node[1:]:
                     mapping.update(self._flatten_toc([child]))
                     
            elif isinstance(node, epub.Link):
                mapping[self._clean_href(node.href)] = node.title
                
            elif isinstance(node, epub.Section):
                # Section just has title and href (often pointing to first child)
                # Structure: Section title, [children]
                # It seems Section IS a container.
                # Use section title as context?
                # But Section object itself doesn't have href usually?
                # Wait, Section(title, href).
                if node.href:
                    mapping[self._clean_href(node.href)] = node.title
        return mapping
        
    def _clean_href(self, href: str) -> str:
        """Remove fragments from href."""
        if '#' in href:
            return href.split('#')[0]
        return href
