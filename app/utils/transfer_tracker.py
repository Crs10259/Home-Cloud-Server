import time
import io
from flask import request, g, Response
from typing import Callable
from functools import wraps
from werkzeug.datastructures import FileStorage

class TransferSpeedTracker:
    """
    Utility class to track file uploads and downloads with speed metrics
    """
    
    def __init__(self) -> None:
        self.start_time = None
        self.end_time = None
        self.file_size = 0
        self.bytes_transferred = 0
        self.is_tracking = False
    
    def start(self, file_size: int = None) -> 'TransferSpeedTracker':
        """Start tracking a file transfer"""
        self.start_time = time.time()
        self.file_size = file_size
        self.bytes_transferred = 0
        self.is_tracking = True
        return self
    
    def update(self, bytes_count: int) -> None:
        """Update bytes transferred count"""
        if not self.is_tracking:
            return
        
        self.bytes_transferred += bytes_count
    
    def stop(self) -> dict:
        """Stop tracking and return metrics"""
        if not self.is_tracking:
            return None
        
        self.end_time = time.time()
        self.is_tracking = False
        
        duration = self.end_time - self.start_time
        speed = self.bytes_transferred / duration if duration > 0 else 0
        
        return {
            'file_size': self.file_size or self.bytes_transferred,
            'duration': duration,
            'speed': speed,
            'start_time': self.start_time,
            'end_time': self.end_time
        }

class TrackableFileStorage(FileStorage):
    """
    Wrapper around FileStorage that tracks read operations
    """
    
    def __init__(self, file_storage: FileStorage, tracker: TransferSpeedTracker) -> None:
        super().__init__(
            stream=file_storage.stream,
            filename=file_storage.filename,
            name=file_storage.name,
            content_type=file_storage.content_type,
            content_length=file_storage.content_length,
            headers=file_storage.headers,
        )
        self.tracker = tracker
        self._file = TrackableFile(self.stream, self.tracker)
    
    def save(self, dst: str, buffer_size: int = 16384) -> None:
        """
        Save the file to a destination path, tracking bytes written
        """
        self._file.seek(0)
        with open(dst, 'wb') as f:
            while True:
                buf = self._file.read(buffer_size)
                if not buf:
                    break
                f.write(buf)

class TrackableFile:
    """
    File-like wrapper that tracks read operations
    """
    
    def __init__(self, fileobj: io.BytesIO, tracker: TransferSpeedTracker) -> None:
        self.fileobj = fileobj
        self.tracker = tracker
    
    def read(self, size: int = -1) -> bytes:
        data = self.fileobj.read(size)
        self.tracker.update(len(data))
        return data
    
    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        return self.fileobj.seek(offset, whence)
    
    def tell(self) -> int:
        return self.fileobj.tell()
    
    def close(self) -> None:
        return self.fileobj.close()

class TrackableResponse:
    """
    Response wrapper that tracks bytes sent
    """
    
    def __init__(self, response: Response, tracker: TransferSpeedTracker) -> None:
        self.response = response
        self.tracker = tracker
        
        # Wrap the response data to track bytes
        original_data = self.response.data
        self.response.data = original_data
        self.tracker.update(len(original_data))
    
    def __getattr__(self, name):
        return getattr(self.response, name)

def track_upload() -> Callable:
    """Decorator to track file upload speed and time"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store file size before reading it
            file = request.files.get('file')
            if not file:
                return f(*args, **kwargs)
            
            # Create tracker and wrapped file
            tracker = TransferSpeedTracker().start(file.content_length)
            request.files['file'] = TrackableFileStorage(file, tracker)
            
            # Store tracker in g for access in the view
            g.upload_tracker = tracker
            
            result = f(*args, **kwargs)
            
            # Get metrics after function completes
            metrics = tracker.stop()
            g.upload_metrics = metrics
            
            return result
        return decorated_function
    return decorator

def track_download() -> Callable:
    """Decorator to track file download speed and time"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create tracker
            tracker = TransferSpeedTracker().start()
            g.download_tracker = tracker
            
            # Get the response
            response = f(*args, **kwargs)
            
            # Wrap the response to track bytes sent
            trackable_response = TrackableResponse(response, tracker)
            
            # Get metrics
            metrics = tracker.stop()
            g.download_metrics = metrics
            
            return trackable_response
        return decorated_function
    return decorator 