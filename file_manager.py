import json
import os

class FileManager:
    def __init__(self):
        self.channels = {} # chan_num -> {type, filename, data, pos}
        self.storage_dir = "basic_storage"
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _get_path(self, filename):
        return os.path.join(self.storage_dir, filename + ".json")

    def create(self, filename, file_type, rec_len=None, key_len=None):
        path = self._get_path(filename)
        # Use a structure that includes metadata
        file_content = {
            "_metadata": {
                "type": file_type,
                "rec_len": rec_len,
                "key_len": key_len
            },
            "records": {}
        }
        with open(path, 'w') as f:
            json.dump(file_content, f, indent=2)

    def open(self, channel, filename, file_type=None, rec_len=None):
        path = self._get_path(filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {filename}")
        
        with open(path, 'r') as f:
            try:
                file_content = json.load(f)
            except json.JSONDecodeError:
                # Handle empty or corrupted file gracefully if needed, or re-raise
                # For now assuming valid JSON if file exists
                file_content = {"records": {}} # Fallback?

        # If the file uses the old format (no metadata), migrate it or handle it
        if "_metadata" not in file_content:
            metadata = {
                "type": file_type or "SERIAL",
                "rec_len": rec_len,
                "key_len": None
            }
            records = file_content
        else:
            metadata = file_content["_metadata"]
            records = file_content["records"]
        
        self.channels[channel] = {
            'type': metadata['type'],
            'filename': filename,
            'data': records,
            'metadata': metadata,
            'pos': 0
        }

    def close(self, channel):
        if channel in self.channels:
            chan = self.channels[channel]
            path = self._get_path(chan['filename'])
            file_content = {
                "_metadata": chan['metadata'],
                "records": chan['data']
            }
            with open(path, 'w') as f:
                json.dump(file_content, f, indent=2)
            del self.channels[channel]

    def write(self, channel, key=None, ind=None, values=None):
        if channel not in self.channels:
            raise RuntimeError(f"Channel {channel} not open")
        
        chan = self.channels[channel]
        data = chan['data']
        
        if chan['type'] == 'INDEXED' and ind is not None:
            data[str(ind)] = values
        elif chan['type'] in ('DIRECT', 'SORT') and key is not None:
            data[str(key)] = values
        elif chan['type'] == 'SERIAL':
            data[str(len(data))] = values
        else:
            raise RuntimeError(f"Invalid write operation on {chan['type']} file")

    def read(self, channel, key=None, ind=None):
        if channel not in self.channels:
            raise RuntimeError(f"Channel {channel} not open")
        
        chan = self.channels[channel]
        data = chan['data']
        
        if chan['type'] == 'INDEXED' and ind is not None:
            return data.get(str(ind))
        elif chan['type'] in ('DIRECT', 'SORT') and key is not None:
            return data.get(str(key))
        elif chan['type'] == 'SERIAL':
            val = data.get(str(chan['pos']))
            if val is not None:
                chan['pos'] += 1
            return val
        
        return None

    def extract(self, channel, key=None, ind=None):
        """Same as read, but would normally lock the record in Thoroughbred."""
        return self.read(channel, key=key, ind=ind)

    def erase(self, filename):
        path = self._get_path(filename)
        if os.path.exists(path):
            os.remove(path)
