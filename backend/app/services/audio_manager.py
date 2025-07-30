"""
Audio File Manager Service for the Audio Processing Backend.
Provides efficient audio file management using AVL tree and caching.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

from app.core.config import settings
from app.core.errors import AudioFileNotFoundError, AudioFormatNotSupportedError

logger = logging.getLogger(__name__)


@dataclass
class AudioFileNode:
    """Node in the AVL tree representing an audio file."""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    format: str
    upload_time: str
    last_accessed: str
    access_count: int
    tags: List[str]
    metadata: Dict[str, Any]
    processing_history: List[Dict[str, Any]]
    height: int = 1
    left: Optional['AudioFileNode'] = None
    right: Optional['AudioFileNode'] = None


class AVLAudioTree:
    """AVL Tree for efficient audio file management."""
    
    def __init__(self):
        self.root: Optional[AudioFileNode] = None
        self.file_count = 0
        self.total_size = 0
        self.cache: Dict[str, AudioFileNode] = {}
        self.cache_size = 1000
        
    def _height(self, node: Optional[AudioFileNode]) -> int:
        """Get height of a node."""
        if node is None:
            return 0
        return node.height
    
    def _balance_factor(self, node: AudioFileNode) -> int:
        """Get balance factor of a node."""
        return self._height(node.left) - self._height(node.right)
    
    def _update_height(self, node: AudioFileNode):
        """Update height of a node."""
        node.height = max(self._height(node.left), self._height(node.right)) + 1
    
    def _rotate_right(self, y: AudioFileNode) -> AudioFileNode:
        """Right rotation."""
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _rotate_left(self, x: AudioFileNode) -> AudioFileNode:
        """Left rotation."""
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def _balance(self, node: AudioFileNode) -> AudioFileNode:
        """Balance the AVL tree."""
        self._update_height(node)
        balance = self._balance_factor(node)
        
        # Left Left Case
        if balance > 1 and self._balance_factor(node.left) >= 0:
            return self._rotate_right(node)
        
        # Right Right Case
        if balance < -1 and self._balance_factor(node.right) <= 0:
            return self._rotate_left(node)
        
        # Left Right Case
        if balance > 1 and self._balance_factor(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        # Right Left Case
        if balance < -1 and self._balance_factor(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    def insert(self, audio_file: AudioFileNode) -> None:
        """Insert a new audio file into the AVL tree."""
        self.root = self._insert_recursive(self.root, audio_file)
        self.file_count += 1
        self.total_size += audio_file.file_size
        
        # Update cache
        self.cache[audio_file.file_id] = audio_file
        if len(self.cache) > self.cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
    
    def _insert_recursive(self, node: Optional[AudioFileNode], audio_file: AudioFileNode) -> AudioFileNode:
        """Recursive insert with balancing."""
        if node is None:
            return audio_file
        
        if audio_file.file_id < node.file_id:
            node.left = self._insert_recursive(node.left, audio_file)
        elif audio_file.file_id > node.file_id:
            node.right = self._insert_recursive(node.right, audio_file)
        else:
            # Update existing node
            node.last_accessed = datetime.now().isoformat()
            node.access_count += 1
            return node
        
        return self._balance(node)
    
    def find(self, file_id: str) -> Optional[AudioFileNode]:
        """Find an audio file by ID."""
        # Check cache first
        if file_id in self.cache:
            node = self.cache[file_id]
            node.last_accessed = datetime.now().isoformat()
            node.access_count += 1
            return node
        
        # Search in tree
        node = self._find_recursive(self.root, file_id)
        if node:
            self.cache[file_id] = node
            if len(self.cache) > self.cache_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
        
        return node
    
    def _find_recursive(self, node: Optional[AudioFileNode], file_id: str) -> Optional[AudioFileNode]:
        """Recursive find."""
        if node is None or node.file_id == file_id:
            if node:
                node.last_accessed = datetime.now().isoformat()
                node.access_count += 1
            return node
        
        if file_id < node.file_id:
            return self._find_recursive(node.left, file_id)
        return self._find_recursive(node.right, file_id)
    
    def delete(self, file_id: str) -> bool:
        """Delete an audio file from the tree."""
        if file_id in self.cache:
            del self.cache[file_id]
        
        self.root = self._delete_recursive(self.root, file_id)
        if self.root:
            self.file_count -= 1
            return True
        return False
    
    def _delete_recursive(self, node: Optional[AudioFileNode], file_id: str) -> Optional[AudioFileNode]:
        """Recursive delete with balancing."""
        if node is None:
            return node
        
        if file_id < node.file_id:
            node.left = self._delete_recursive(node.left, file_id)
        elif file_id > node.file_id:
            node.right = self._delete_recursive(node.right, file_id)
        else:
            # Node to be deleted found
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            
            # Node with two children
            temp = self._min_value_node(node.right)
            node.file_id = temp.file_id
            node.filename = temp.filename
            node.file_path = temp.file_path
            node.file_size = temp.file_size
            node.duration = temp.duration
            node.sample_rate = temp.sample_rate
            node.channels = temp.channels
            node.bit_depth = temp.bit_depth
            node.format = temp.format
            node.upload_time = temp.upload_time
            node.last_accessed = temp.last_accessed
            node.access_count = temp.access_count
            node.tags = temp.tags
            node.metadata = temp.metadata
            node.processing_history = temp.processing_history
            
            node.right = self._delete_recursive(node.right, temp.file_id)
        
        return self._balance(node) if node else None
    
    def _min_value_node(self, node: AudioFileNode) -> AudioFileNode:
        """Find the node with minimum value."""
        current = node
        while current.left is not None:
            current = current.left
        return current
    
    def get_all_files(self) -> List[AudioFileNode]:
        """Get all audio files in order."""
        files = []
        self._inorder_traversal(self.root, files)
        return files
    
    def _inorder_traversal(self, node: Optional[AudioFileNode], files: List[AudioFileNode]):
        """Inorder traversal to get sorted list."""
        if node:
            self._inorder_traversal(node.left, files)
            files.append(node)
            self._inorder_traversal(node.right, files)
    
    def search_by_tags(self, tags: List[str]) -> List[AudioFileNode]:
        """Search files by tags."""
        results = []
        self._search_by_tags_recursive(self.root, tags, results)
        return results
    
    def _search_by_tags_recursive(self, node: Optional[AudioFileNode], tags: List[str], results: List[AudioFileNode]):
        """Recursive search by tags."""
        if node:
            self._search_by_tags_recursive(node.left, tags, results)
            if any(tag in node.tags for tag in tags):
                results.append(node)
            self._search_by_tags_recursive(node.right, tags, results)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tree statistics."""
        return {
            'total_files': self.file_count,
            'total_size': self.total_size,
            'cache_size': len(self.cache),
            'tree_height': self._height(self.root),
            'average_file_size': self.total_size / self.file_count if self.file_count > 0 else 0
        }


class AudioFileManager:
    """High-level audio file manager with AVL tree backend."""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or settings.uploads_dir)
        self.avl_tree = AVLAudioTree()
        self.index_file = self.storage_path / "audio_index.json"
        self.load_index()
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Audio file manager initialized with storage path: {self.storage_path}")
    
    def generate_file_id(self, filename: str, file_size: int) -> str:
        """Generate unique file ID."""
        content = f"{filename}_{file_size}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def add_audio_file(self, file_path: str, metadata: Dict[str, Any]) -> AudioFileNode:
        """Add a new audio file to the manager."""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                raise AudioFileNotFoundError(f"File not found: {file_path}")
            
            # Generate file ID
            filename = file_path.name
            file_size = file_path.stat().st_size
            file_id = self.generate_file_id(filename, file_size)
            
            # Create audio file node
            audio_file = AudioFileNode(
                file_id=file_id,
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                duration=metadata.get('duration', 0.0),
                sample_rate=metadata.get('sample_rate', 44100),
                channels=metadata.get('channels', 2),
                bit_depth=metadata.get('bit_depth', 16),
                format=metadata.get('format', 'wav'),
                upload_time=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                access_count=1,
                tags=metadata.get('tags', []),
                metadata=metadata,
                processing_history=[]
            )
            
            # Add to AVL tree
            self.avl_tree.insert(audio_file)
            
            # Save index
            await self.save_index()
            
            logger.info(f"Added audio file: {file_id} - {filename}")
            return audio_file
            
        except Exception as e:
            logger.error(f"Error adding audio file: {e}")
            raise
    
    async def get_audio_file(self, file_id: str) -> Optional[AudioFileNode]:
        """Get audio file by ID."""
        return self.avl_tree.find(file_id)
    
    async def delete_audio_file(self, file_id: str) -> bool:
        """Delete audio file."""
        try:
            node = self.avl_tree.find(file_id)
            if node:
                # Remove physical file
                file_path = Path(node.file_path)
                if file_path.exists():
                    file_path.unlink()
                
                # Remove from tree
                success = self.avl_tree.delete(file_id)
                if success:
                    await self.save_index()
                    logger.info(f"Deleted audio file: {file_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting audio file: {e}")
            return False
    
    async def update_processing_history(self, file_id: str, effect: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Update processing history for a file."""
        node = self.avl_tree.find(file_id)
        if node:
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'effect': effect,
                'parameters': parameters,
                'result': result
            }
            node.processing_history.append(history_entry)
            await self.save_index()
    
    async def search_files(self, query: str = "", tags: List[str] = None, limit: int = 100) -> List[AudioFileNode]:
        """Search files by query and tags."""
        all_files = self.avl_tree.get_all_files()
        results = []
        
        for file in all_files:
            # Check query match
            if query and query.lower() not in file.filename.lower():
                continue
            
            # Check tags match
            if tags and not any(tag in file.tags for tag in tags):
                continue
            
            results.append(file)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def get_popular_files(self, limit: int = 10) -> List[AudioFileNode]:
        """Get most accessed files."""
        all_files = self.avl_tree.get_all_files()
        sorted_files = sorted(all_files, key=lambda x: x.access_count, reverse=True)
        return sorted_files[:limit]
    
    async def get_recent_files(self, limit: int = 10) -> List[AudioFileNode]:
        """Get recently uploaded files."""
        all_files = self.avl_tree.get_all_files()
        sorted_files = sorted(all_files, key=lambda x: x.upload_time, reverse=True)
        return sorted_files[:limit]
    
    def load_index(self):
        """Load index from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    
                # Rebuild AVL tree
                for file_data in data.get('files', []):
                    try:
                        # Convert dict back to AudioFileNode, handling missing fields
                        node = AudioFileNode(
                            file_id=file_data.get('file_id', ''),
                            filename=file_data.get('filename', ''),
                            file_path=file_data.get('file_path', ''),
                            file_size=file_data.get('file_size', 0),
                            duration=file_data.get('duration', 0.0),
                            sample_rate=file_data.get('sample_rate', 44100),
                            channels=file_data.get('channels', 1),
                            bit_depth=file_data.get('bit_depth', 16),
                            format=file_data.get('format', 'wav'),
                            upload_time=file_data.get('upload_time', datetime.now().isoformat()),
                            last_accessed=file_data.get('last_accessed', datetime.now().isoformat()),
                            access_count=file_data.get('access_count', 0),
                            tags=file_data.get('tags', []),
                            metadata=file_data.get('metadata', {}),
                            processing_history=file_data.get('processing_history', [])
                        )
                        self.avl_tree.insert(node)
                    except Exception as e:
                        logger.warning(f"Error loading file data: {e}")
                        continue
                
                logger.info(f"Loaded {len(data.get('files', []))} audio files from index")
                
        except Exception as e:
            logger.error(f"Error loading index: {e}")
    
    async def save_index(self):
        """Save index to disk."""
        try:
            files = self.avl_tree.get_all_files()
            data = {
                'files': [asdict(file) for file in files],
                'statistics': self.avl_tree.get_statistics(),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.index_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved index with {len(files)} files")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        tree_stats = self.avl_tree.get_statistics()
        return {
            **tree_stats,
            'storage_path': str(self.storage_path),
            'index_file': str(self.index_file)
        } 