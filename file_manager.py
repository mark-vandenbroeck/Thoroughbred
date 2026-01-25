import json
import os

class FileManager:
    def __init__(self):
        self.channels = {} # chan_num -> {type, filename, data, pos}
        self.storage_dir = "basic_storage"
        self.disks = {} # D0 -> path, D1 -> path
        self.program_paths = ['.']
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
                            if key == 'PATH':
                                # Split by commas, strip, and store
                                self.program_paths = [p.strip() for p in val.split(',')]
                            else:
                                self.disks[key] = val
                                if not os.path.exists(val):
                                    try:
                                        os.makedirs(val)
                                    except: pass # Just warn?
        except Exception as e:
            print(f"Warning: Error loading IPLINPUT: {e}")

    def find_program(self, filename):
        """Searches for a program in the defined program_paths."""
        trial_names = [filename]
        if not filename.lower().endswith('.bas'):
            trial_names.append(filename + ".bas")
            trial_names.append(filename + ".BAS")
            
        for path in self.program_paths:
            for trial in trial_names:
                full_path = os.path.join(path, trial)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    return full_path
        return None

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
        
        if file_type == 'TEXT':
             # Create empty raw text file
             # Ensure directory exists
             os.makedirs(os.path.dirname(path), exist_ok=True)
             # Remove .json extension for TEXT files or keep common naming?
             # Implementation plan said "create raw text file".
             # _get_path appends .json. If I use .txt or no extension, I need to adjust logic.
             # Easier to use a different extension for TEXT or just no extension?
             # For consistency with _get_path, let's strip .json suffix if desired, or just use it.
             # User manual says "flat file".
             # Let's use .txt for clarity if type is TEXT, or just override path?
             # Re-using _get_path which adds .json is simplest for path resolution but weird for "TEXT" file.
             # However, FileManager logic assumes .json for everything else.
             # Let's hack _get_path or just use `path` (which has .json) but write raw text.
             # It acts as "system text file".
             # Let's strip .json for TEXT files to be "compatible with system text files".
             if path.endswith('.json'): path = path[:-5]
             
             with open(path, 'w') as f:
                 f.write("")
             return

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
        
        # Check if we should treat as TEXT (explicit opt or existing file check?)
        # Implementation Plan: "If file_type == 'TEXT' (passed from OPEN directive)"
        # Note: _get_path returns path with .json extension.
        # If we created it without .json, we need to find it differently.
        # Update _get_path logic? Or search trial names.
        
        real_path = path
        is_text = (file_type == 'TEXT')
        
        if is_text:
             # Try without .json
             if path.endswith('.json'):
                 base_path = path[:-5]
                 if os.path.exists(base_path):
                     real_path = base_path
                 elif not os.path.exists(path):
                     # If neither exists
                     raise FileNotFoundError(f"File not found: {filename}")
        
        if not os.path.exists(real_path):
            raise FileNotFoundError(f"File not found: {filename}")
        
        if is_text:
            with open(real_path, 'r', encoding='latin-1') as f: # binary-safeish string
                data = f.read()
            
            self.channels[channel] = {
                'type': 'TEXT',
                'filename': filename,
                'path': real_path,
                'data': data,
                'metadata': {},
                'pos': 0,
                'last_key': None
            }
            return

        with open(real_path, 'r') as f:
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
            
            if chan['type'] == 'TEXT':
                with open(path, 'w', encoding='latin-1') as f:
                    f.write(chan['data'])
                del self.channels[channel]
                return

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
        elif chan['type'] == 'TEXT':
            # values should be a string to write
            # ind is valid. If None, use current pos?
            # "A WRITE RECORD directive simply writes ... starting at the current position or the position specified by the IND="
            vals = str(values)
            start = ind if ind is not None else chan.get('pos', 0)
            
            # Extend string if needed
            current_len = len(data)
            if start > current_len:
                data += "\0" * (start - current_len)
            
            # Overwrite logic
            # data is string. Strings are immutable in Python.
            pre = data[:start]
            post = data[start+len(vals):]
            chan['data'] = pre + vals + post
            
            # Update position (usually after write)
            chan['pos'] = start + len(vals)
            
        else:
            raise RuntimeError(f"Invalid write operation on {chan['type']} file")

    def read(self, channel, key=None, ind=None, advance_pointer=True, update_ptr_on_error=True):
        if channel not in self.channels:
            raise RuntimeError(f"Channel {channel} not open")
        
        chan = self.channels[channel]
        data = chan['data']
        
        if chan['type'] == 'INDEXED' and ind is not None:
            s_key = str(ind)
            if s_key in data:
                chan['last_key'] = s_key
                return data.get(s_key)
            else:
                if update_ptr_on_error: chan['last_key'] = s_key
                return None
                
        elif chan['type'] in ('DIRECT', 'SORT') and key is not None:
            s_key = str(key)
            if s_key in data:
                chan['last_key'] = s_key
                return data.get(s_key)
            else:
                if update_ptr_on_error: chan['last_key'] = s_key
                return None
                
            if val is not None and advance_pointer:
                chan['pos'] += 1
            return val
            
        elif chan['type'] == 'TEXT':
             # TEXT file read
             # Need start (ind) and length (siz)
             # "The actual READ is terminated by an End of File... or SIZ... or separator"
             # If SIZ is not provided, max string size.
             # Logic is complex, handled partly here.
             # Return raw string from position?
             # Let's implement a direct 'read_chunk' logic or handle it via returned object?
             # Interpreter calls read().
             # interpreter.py expects read() to return a value.
             # For READ (SERIAL/INDEXED), it returns a record (list/dict/string).
             # For TEXT, we return a string Chunk?
             # We need 'siz' parameter here or handle it in interpreter.
             # The arguments to read() are key/ind.
             # We should probably extend read() to accept 'siz' or handle slicing in interpreter if read() returns full tail?
             # Returning full tail is inefficient.
             # Let's rely on 'ind' being passed. If 'siz' is needed, maybe passed as key? Or a new arg?
             # For now, let's return the whole string from 'ind' and let Interpreter slice/scan it?
             # Or better: Add 'siz' arg to read().
             start = ind if ind is not None else chan.get('pos', 0)
             
             # If siz not passed, we don't know how much to read.
             # But existing read() signature doesn't have siz.
             # Let's return the rest of the string for now, and let interpreter process it.
             # Or we can update read signature later.
             # Wait, I can access 'data' directly in interpreter if I need complex logic, 
             # but better to abstract it.
             # I'll return the string from start.
             
             # Interpreter logic for TEXT file will likely need to scan for delimiters.
             # So giving subsequent string is appropriate.
             if start >= len(data):
                 return None # EOF
             
             res = data[start:]
             # Note: pos update happens in interpreter based on consumption?
             # TEXT file pos tracking is tricky if we scan.
             # We'll leave pos update to caller or default to not advancing here implies caller manages it?
             # For now, return remaining data.
             return res
        
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
