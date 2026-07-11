from ..common import *
from ..debug import DEBUG
from ..models import SoundEntry

class BNKEditor:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        self.data = None
        self._sound_map = None
        self.load_file()

    def _build_sound_map(self):

        if self._sound_map is not None:
            return

        DEBUG.log(f"Building sound map for {self.file_path.name}...")
        self._sound_map = {}

        search_pattern = b'\x01\x00\x04\x00\x00'
        offset = 0
        while True:
            try:
                offset = self.data.index(search_pattern, offset)
                
                id_offset = offset + 5
                if id_offset + 4 <= len(self.data):
                    source_id = struct.unpack('<I', self.data[id_offset:id_offset+4])[0]
                    
                    entry_start_offset = offset - 4 
                    
                    if source_id not in self._sound_map:
                        self._sound_map[source_id] = []
                    self._sound_map[source_id].append(entry_start_offset)

                offset += len(search_pattern)
            except ValueError:
                break 
        DEBUG.log(f"Sound map for {self.file_path.name} built. Found {len(self._sound_map)} unique sound IDs.")

    def load_file(self):
        with open(self.file_path, 'rb') as f:
            self.data = bytearray(f.read())

    def save_file(self, output_path: Optional[str] = None):
        if output_path is None:
            output_path = self.file_path
            
        with open(output_path, 'wb') as f:
            f.write(self.data)

    def find_sound_by_source_id(self, source_id: int, expected_size: Optional[int] = None) -> List[SoundEntry]:
        self._build_sound_map() 
        
        offsets = self._sound_map.get(source_id)
        if not offsets:
            return []
        
        found_entries = []
        for offset in offsets:
            entry = self._parse_sound_entry(offset)
            if entry:
                if expected_size is None or entry.file_size == expected_size:
                    found_entries.append(entry)
        return found_entries
        
    def find_all_sounds(self) -> List[SoundEntry]:
     
        self._build_sound_map()
        all_entries = []
        for source_id, offsets in self._sound_map.items():
            for offset in offsets:
                entry = self._parse_sound_entry(offset)
                if entry:
                    all_entries.append(entry)
        return all_entries

    def _parse_sound_entry(self, offset: int) -> Optional[SoundEntry]:
        try:
            if offset + 19 > len(self.data):
                return None
            
            sound_id = struct.unpack('<I', self.data[offset:offset+4])[0]

            source_id_offset = offset + 9
            source_id = struct.unpack('<I', self.data[source_id_offset:source_id_offset+4])[0]
            
            file_size_offset = source_id_offset + 4
            file_size = struct.unpack('<I', self.data[file_size_offset:file_size_offset+4])[0]
            
            fx_flag_offset = file_size_offset + 5 
            override_fx = self.data[fx_flag_offset] == 0x01
            
            return SoundEntry(
                offset=offset,
                sound_id=sound_id,
                source_id=source_id,
                file_size=file_size,
                override_fx=override_fx
            )
        except (struct.error, IndexError):
            return None
            
    def modify_sound(self, source_id: int, override_fx: Optional[bool] = None, 
                     new_size: Optional[int] = None, find_by_size: Optional[int] = None):
        entries = self.find_sound_by_source_id(source_id, find_by_size)
        
        if not entries:
            # DEBUG.log(f"Sound with Source ID {source_id} (and size {find_by_size}) not found in BNK", "WARNING")
            return False
            
        modified = False
        for entry in entries:
            # DEBUG.log(f"Modifying entry in BNK at offset 0x{entry.offset:08X} (ID: {entry.source_id}, current size: {entry.file_size})")

            if override_fx is not None:
                fx_flag_offset = entry.offset + 18
                new_byte = 0x01 if override_fx else 0x00
                self.data[fx_flag_offset] = new_byte
                # DEBUG.log(f"  Override FX changed to: {override_fx}")
                modified = True
                
            if new_size is not None:
                if new_size > 0xFFFFFFFF:
                    # DEBUG.log(f"  Size {new_size} is too large", "ERROR")
                    continue
                    
                file_size_offset = entry.offset + 13
                struct.pack_into('<I', self.data, file_size_offset, new_size)
                # DEBUG.log(f"  File size changed from {entry.file_size} to: {new_size}")
                modified = True
                
        return modified

class BnkInfoLoader(QtCore.QThread):
    info_loaded = QtCore.pyqtSignal(int, object, object)  # source_id, original_info, modified_info

    def __init__(self, parent, source_id, bnk_files_info, mod_p_path, wems_base_path):
        super().__init__(parent)
        self.source_id = source_id
        self.bnk_files_info = bnk_files_info 
        self.mod_p_path = mod_p_path
        self.wems_base_path = wems_base_path
        self.parent_app = parent
        
    def run(self):
        original_bnk_info, original_bnk_path = self.find_info_in_bnks(self.bnk_files_info, self.source_id, is_mod=False)
        if original_bnk_info:
            DEBUG.log(f"Original information for ID {self.source_id} found in BNK: {os.path.basename(original_bnk_path)}")
        else:
            DEBUG.log(f"Original information for ID {self.source_id} not found in any BNK.")

        mod_bnk_paths_info = []
        for bnk_path, bnk_type in self.bnk_files_info:
            if bnk_type == 'sfx':
                base_for_relpath = os.path.join(self.wems_base_path, "SFX")
                rel_path = os.path.relpath(bnk_path, base_for_relpath)
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            else:
                base_for_relpath = self.wems_base_path
                rel_path = os.path.relpath(bnk_path, base_for_relpath)
                mod_bnk_path = os.path.join(self.mod_p_path, "OPP", "Content", "WwiseAudio", "Windows", rel_path)
            
            if os.path.exists(mod_bnk_path):
                mod_bnk_paths_info.append((mod_bnk_path, bnk_type))
        
        modified_bnk_info, modified_bnk_path = self.find_info_in_bnks(mod_bnk_paths_info, self.source_id, is_mod=True)
        if modified_bnk_info:
            DEBUG.log(f"Modified information for ID {self.source_id} found in BNK: {os.path.basename(modified_bnk_path)}")
        else:
            if mod_bnk_paths_info:
                 DEBUG.log(f"Modified information for ID {self.source_id} not found.")

        self.info_loaded.emit(self.source_id, original_bnk_info, modified_bnk_info)

    def find_info_in_bnks(self, bnk_paths_info, source_id, is_mod=False):
        cache_name = 'bnk_cache_mod' if is_mod else 'bnk_cache_orig'
        cache = getattr(self.parent_app, cache_name, {})
        
        for bnk_path, bnk_type in bnk_paths_info:
            if bnk_path in cache and source_id in cache[bnk_path]:
                return cache[bnk_path][source_id], bnk_path

            try:
                editor = BNKEditor(bnk_path)
                entries = editor.find_sound_by_source_id(source_id)
                if entries:
                    entry = entries[0]
                    
                    if bnk_path not in cache:
                        cache[bnk_path] = {}
                    cache[bnk_path][source_id] = entry
                    setattr(self.parent_app, cache_name, cache)
                    
                    return entry, bnk_path
            except Exception as e:
                DEBUG.log(f"Error reading BNK {bnk_path}: {e}", "WARNING")
                continue
        
        return None, None
