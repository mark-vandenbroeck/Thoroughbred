import json
import os

class FileManager:
    def __init__(self):
        self.channels = {} # chan_num -> {type, filename, data, pos}
        self.storage_dir = "basic_storage"
        self.disks = {} # D0 -> path, D1 -> path
        self.load_iplinput()
        
        # Ensure default storage exists if no disks
        if not self.disks and not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def load_iplinput(self):
        try:
            if os.path.exists('IPLINPUT'):
                with open('IPLINPUT', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'): continue
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip().upper()
                            val = val.strip()
                            self.disks[key] = val
                            if not os.path.exists(val):
                                try:
                                    os.makedirs(val)
                                except: pass # Just warn?
        except Exception as e:
            print(f"Warning: Error loading IPLINPUT: {e}")

    def _get_path(self, filename, disk_num=None, search=False):
        # 1. If explicit disk provided (for CREATE)
        if disk_num is not None:
            # disk_num comes as int usually, e.g. 0 -> D0, 10 -> DA?
            # User said: "bijv. 0 voor D0, 1 voor D1".
            # Mapping heuristic: 0-9 -> D0-D9. >9?
            # Or disk name passed directly? User said "disk-num" is integer.
            # Let's assume D + str(disk_num) for now.
            # What if disk_num is a string "A"? User said "disk is een integer waarde".
            # But keys are D0, DA...
            # Maybe 0->D0, 1->D1.
            key = f"D{disk_num}"
            if key in self.disks:
                return os.path.join(self.disks[key], filename + ".json")
            else:
                 # Fallback to default or error?
                 # If explicit disk request fails, maybe default dir?
                 return os.path.join(self.storage_dir, filename + ".json")

        # 2. Search existing (for OPEN)
        if search:
            # Sort disks alphabetically
            sorted_disks = sorted(self.disks.keys())
            for key in sorted_disks:
                path = os.path.join(self.disks[key], filename + ".json")
                if os.path.exists(path):
                    return path
        
        # 3. Default (current dir or standard storage)
        return os.path.join(self.storage_dir, filename + ".json")

    def create(self, filename, file_type, rec_len=None, key_len=None, disk_num=None):
        path = self._get_path(filename, disk_num=disk_num, search=False)
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
        path = self._get_path(filename, search=True) # Search disks
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
            'path': path, # Store the actual path
            'data': records,
            'metadata': metadata,
            'pos': 0,
            'last_key': None # Track last accessed key for REMOVE without KEY
        }

    def close(self, channel):
        if channel in self.channels:
            chan = self.channels[channel]
            path = chan.get('path') or self._get_path(chan['filename'])
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
        # print(f"DEBUG: WRITE ch={channel} key={key} ind={ind}")
        
        if chan['type'] == 'INDEXED' and ind is not None:
            data[str(ind)] = values
            chan['last_key'] = str(ind)
        elif chan['type'] in ('DIRECT', 'SORT') and key is not None:
            data[str(key)] = values
            chan['last_key'] = str(key)
        elif chan['type'] == 'SERIAL':
            idx = str(len(data))
            data[idx] = values
            chan['last_key'] = idx
        else:
            raise RuntimeError(f"Invalid write operation on {chan['type']} file")

    def read(self, channel, key=None, ind=None, advance_pointer=True):
        if channel not in self.channels:
            raise RuntimeError(f"Channel {channel} not open")
        
        chan = self.channels[channel]
        data = chan['data']
        
        if chan['type'] == 'INDEXED' and ind is not None:
            chan['last_key'] = str(ind)
            return data.get(str(ind))
        elif chan['type'] in ('DIRECT', 'SORT') and key is not None:
            chan['last_key'] = str(key)
            return data.get(str(key))
        elif chan['type'] == 'SERIAL':
            val = data.get(str(chan['pos']))
            chan['last_key'] = str(chan['pos'])
            if val is not None and advance_pointer:
                chan['pos'] += 1
            return val
        
        return None

    def extract(self, channel, key=None, ind=None):
        return self.read(channel, key=key, ind=ind, advance_pointer=False)

    def remove(self, channel, key=None):
        if channel not in self.channels:
            raise RuntimeError(f"Channel {channel} not open")
        
        chan = self.channels[channel]
        data = chan['data']
        target_key = None

        if key is not None:
            target_key = str(key)
        else:
            if chan['last_key'] is None:
                raise RuntimeError("No current record to remove")
            target_key = chan['last_key']
        
        if target_key in data:
            del data[target_key]
        else:
            raise FileNotFoundError(f"Key {target_key} not found")

    def erase(self, filename):
        path = self._get_path(filename, search=True)
        if os.path.exists(path):
            os.remove(path)

    def get_next_key(self, channel):
        if channel not in self.channels:
            raise RuntimeError(f"Channel {channel} not open") # Interpreted as ERR=13 usually

        chan = self.channels[channel]
        # Only valid for DIRECT / SORT / INDEXED? Docs say DIRECT or SORT.
        if chan['type'] not in ('DIRECT', 'SORT', 'INDEXED'):
            raise RuntimeError("Invalid file type for KEY function") 

        data = chan['data']
        if not data:
            raise EOFError("File is empty") # ERR=2

        keys = sorted(data.keys())
        
        last_key = chan.get('last_key')
        
        if last_key is None:
            # If no record accessed yet, return first key?
            return keys[0]
        
        # Binary search or simple index lookup
        try:
             # Find current position
            if last_key in keys:
                idx = keys.index(last_key)
                if idx + 1 < len(keys):
                    return keys[idx + 1]
                else:
                    raise EOFError("End of file")
            else:
                # Last key might have been deleted or we jumped to a key that doesn't exist?
                # If last_key not in keys (e.g. random READ with non-existent key?), 
                # we should probably look for the next key *after* the value of last_key
                # even if last_key itself isn't there.
                # Let's fallback to finding insertion point.
                import bisect
                idx = bisect.bisect_right(keys, last_key)
                if idx < len(keys):
                    return keys[idx]
                else:
                    raise EOFError("End of file")
                    
        except ValueError:
            raise EOFError("End of file")
