from typing import Dict, Any, Optional
import datetime



class DataProvenanceTracker:
    """Track and manage data provenance across the entire system."""
    
    @staticmethod
    def create_provenance(
        source: str, 
        cache_status: str = 'miss', 
        timestamp: Optional[datetime] = None,
        error: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized provenance record."""
        if timestamp is None:
            timestamp = datetime.datetime.now()
        
        provenance = {
            'source': source,
            'cache_status': cache_status,
            'timestamp': timestamp.isoformat(),
        }
        
        if error:
            provenance['error'] = error
        if note:
            provenance['note'] = note
        
        return provenance
    
    @staticmethod
    def merge_provenance(*provenance_records: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple provenance records into a single record."""
        if not provenance_records:
            return {}
        
        merged = {
            'sources': [],
            'timestamps': [],
            'cache_statuses': [],
        }
        
        for record in provenance_records:
            if 'source' in record:
                merged['sources'].append(record['source'])
            if 'timestamp' in record:
                merged['timestamps'].append(record['timestamp'])
            if 'cache_status' in record:
                merged['cache_statuses'].append(record['cache_status'])
            if 'error' in record:
                merged['error'] = record['error']
            if 'note' in record:
                merged['note'] = record['note']
        
        # Get earliest timestamp
        if merged['timestamps']:
            merged['first_timestamp'] = min(merged['timestamps'])
            merged['last_timestamp'] = max(merged['timestamps'])
        
        return merged
    
    @staticmethod
    def get_data_lineage(provenance_record: Dict[str, Any]) -> str:
        """Generate a human-readable data lineage string."""
        if 'sources' in provenance_record:
            sources = ', '.join(provenance_record['sources'])
        else:
            sources = provenance_record.get('source', 'unknown')
        
        cache_status = provenance_record.get('cache_status', 'unknown')
        timestamp = provenance_record.get('first_timestamp', 'unknown')
        
        return f"Data from {sources} ({cache_status}) at {timestamp}"